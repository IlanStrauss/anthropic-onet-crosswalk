"""
Build Anthropic API Task → O*NET Crosswalk
==========================================

This script creates a crosswalk linking Anthropic's Claude API task classifications
to O*NET occupational task codes and occupation codes (SOC).

Data Sources:
- Anthropic Economic Index API data (November 2025): HuggingFace
- O*NET Database v29.1: https://www.onetcenter.org/database.html

Methodology:
1. Extract unique task descriptions from Anthropic API data
2. Normalize text (lowercase, remove punctuation, normalize whitespace)
3. Exact match to O*NET Task Statements
4. Fuzzy match remaining tasks (threshold >= 85) using rapidfuzz
5. Enrich with O*NET occupation data, Job Zones, and education requirements

Output:
- master_task_crosswalk.csv: Main crosswalk file
- unmatched_tasks.csv: Tasks that could not be matched

Author: Ilan Strauss / AI Disclosures Project
Date: January 2026
"""

import pandas as pd
from rapidfuzz import fuzz, process
import re
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'processed')
ANTHROPIC_DATA = os.path.join(BASE_DIR, '..', 'release_2026_01_15', 'data', 'intermediate',
                               'aei_raw_1p_api_2025-11-13_to_2025-11-20.csv')
ONET_DIR = os.path.join(RAW_DIR, 'db_29_1_text')

# Fuzzy match threshold
FUZZY_THRESHOLD = 85


def normalize_text(text):
    """Normalize text for matching: lowercase, remove punctuation, normalize whitespace."""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def load_data():
    """Load Anthropic and O*NET data."""
    print("Loading data...")

    # Anthropic API data
    anthropic = pd.read_csv(ANTHROPIC_DATA)

    # O*NET data
    onet_tasks = pd.read_csv(os.path.join(ONET_DIR, 'Task Statements.txt'), sep='\t')
    onet_occs = pd.read_csv(os.path.join(ONET_DIR, 'Occupation Data.txt'), sep='\t')
    job_zones = pd.read_csv(os.path.join(ONET_DIR, 'Job Zones.txt'), sep='\t')
    education = pd.read_csv(os.path.join(ONET_DIR, 'Education, Training, and Experience.txt'), sep='\t')

    return anthropic, onet_tasks, onet_occs, job_zones, education


def extract_anthropic_tasks(anthropic):
    """Extract task descriptions and counts from Anthropic data."""
    print("Extracting Anthropic tasks...")

    task_data = anthropic[
        (anthropic['facet'] == 'onet_task') &
        (anthropic['variable'] == 'onet_task_count')
    ][['cluster_name', 'value']].copy()

    task_data.columns = ['anthropic_task', 'api_count']

    # Exclude placeholder categories
    non_tasks = ['not_classified', 'none']
    task_data = task_data[~task_data['anthropic_task'].str.lower().isin(non_tasks)]

    task_data['task_norm'] = task_data['anthropic_task'].apply(normalize_text)

    print(f"  Found {len(task_data)} unique tasks")
    return task_data


def exact_match(task_data, onet_tasks):
    """Perform exact matching on normalized text."""
    print("Performing exact matching...")

    onet_tasks['task_norm'] = onet_tasks['Task'].apply(normalize_text)
    onet_lookup = onet_tasks.groupby('task_norm').first().reset_index()[
        ['task_norm', 'O*NET-SOC Code', 'Task ID', 'Task', 'Task Type']
    ]

    merged = task_data.merge(onet_lookup, on='task_norm', how='left')
    matched = merged[merged['O*NET-SOC Code'].notna()].copy()
    matched['match_method'] = 'exact'
    matched['match_score'] = 100.0

    unmatched = merged[merged['O*NET-SOC Code'].isna()][
        ['anthropic_task', 'api_count', 'task_norm']
    ]

    print(f"  Exact matches: {len(matched)}")
    print(f"  Remaining for fuzzy matching: {len(unmatched)}")

    return matched, unmatched, onet_tasks


def fuzzy_match(unmatched, onet_tasks, threshold=FUZZY_THRESHOLD):
    """Perform fuzzy matching on remaining tasks."""
    print(f"Performing fuzzy matching (threshold >= {threshold})...")

    onet_choices = list(onet_tasks['task_norm'].unique())
    onet_norm_lookup = onet_tasks.groupby('task_norm').first().reset_index()

    fuzzy_rows = []
    for _, row in unmatched.iterrows():
        result = process.extractOne(row['task_norm'], onet_choices, scorer=fuzz.ratio)
        if result and result[1] >= threshold:
            match_text, score, _ = result
            onet_match = onet_norm_lookup[onet_norm_lookup['task_norm'] == match_text]
            if len(onet_match) > 0:
                onet_row = onet_match.iloc[0]
                fuzzy_rows.append({
                    'anthropic_task': row['anthropic_task'],
                    'api_count': row['api_count'],
                    'task_norm': row['task_norm'],
                    'O*NET-SOC Code': onet_row['O*NET-SOC Code'],
                    'Task ID': onet_row['Task ID'],
                    'Task': onet_row['Task'],
                    'Task Type': onet_row['Task Type'],
                    'match_method': 'fuzzy',
                    'match_score': score
                })

    fuzzy_matched = pd.DataFrame(fuzzy_rows)
    print(f"  Fuzzy matches: {len(fuzzy_matched)}")

    return fuzzy_matched


def enrich_with_onet(matched, onet_occs, job_zones, education):
    """Add O*NET occupation data, job zones, and education."""
    print("Enriching with O*NET attributes...")

    # Add occupation titles and descriptions
    matched = matched.merge(
        onet_occs[['O*NET-SOC Code', 'Title', 'Description']],
        on='O*NET-SOC Code', how='left'
    )

    # Add job zones
    jz_clean = job_zones[['O*NET-SOC Code', 'Job Zone']].drop_duplicates()
    matched = matched.merge(jz_clean, on='O*NET-SOC Code', how='left')

    # Add typical education
    edu_level = education[education['Element Name'] == 'Required Level of Education'][
        ['O*NET-SOC Code', 'Category', 'Data Value']
    ]
    edu_pivot = edu_level.pivot_table(
        index='O*NET-SOC Code', columns='Category',
        values='Data Value', aggfunc='first'
    ).reset_index()

    edu_categories = [c for c in edu_pivot.columns if c != 'O*NET-SOC Code']
    if edu_categories:
        edu_pivot['typical_education'] = edu_pivot[edu_categories].idxmax(axis=1)
        edu_pivot['typical_education_pct'] = edu_pivot[edu_categories].max(axis=1)
        matched = matched.merge(
            edu_pivot[['O*NET-SOC Code', 'typical_education', 'typical_education_pct']],
            on='O*NET-SOC Code', how='left'
        )

    return matched


def save_outputs(matched, task_data, output_dir):
    """Save final crosswalk and unmatched tasks."""
    print("Saving outputs...")

    # Rename columns for final output
    final = matched[[
        'anthropic_task', 'api_count',
        'O*NET-SOC Code', 'Task ID', 'Task', 'Task Type',
        'Title', 'Description',
        'match_method', 'match_score',
        'Job Zone', 'typical_education', 'typical_education_pct'
    ]].copy()

    final.columns = [
        'anthropic_task_description', 'api_usage_count',
        'onet_soc_code', 'onet_task_id', 'onet_task_description', 'onet_task_type',
        'onet_occupation_title', 'onet_occupation_description',
        'match_method', 'match_score',
        'job_zone', 'typical_education', 'typical_education_pct'
    ]

    final = final.sort_values('api_usage_count', ascending=False)
    final.to_csv(os.path.join(output_dir, 'master_task_crosswalk.csv'), index=False)

    # Save unmatched
    matched_tasks = set(matched['anthropic_task'])
    unmatched_final = task_data[~task_data['anthropic_task'].isin(matched_tasks)]
    unmatched_final = unmatched_final.sort_values('api_count', ascending=False)
    unmatched_final[['anthropic_task', 'api_count']].to_csv(
        os.path.join(output_dir, 'unmatched_tasks.csv'), index=False
    )

    return final, unmatched_final


def print_summary(final, task_data, unmatched_final):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("CROSSWALK SUMMARY")
    print("="*60)
    print(f"Total Anthropic tasks: {len(task_data)}")
    print(f"Matched tasks: {len(final)}")
    print(f"Match rate: {len(final) / len(task_data) * 100:.1f}%")
    print(f"\nAPI usage coverage: {final['api_usage_count'].sum() / task_data['api_count'].sum() * 100:.1f}%")
    print(f"\nMatch method breakdown:")
    print(final['match_method'].value_counts().to_string())
    print(f"\nUnique SOC codes: {final['onet_soc_code'].nunique()}")
    print(f"Unmatched tasks: {len(unmatched_final)}")


def main():
    """Main execution."""
    print("="*60)
    print("Building Anthropic → O*NET Task Crosswalk")
    print("="*60 + "\n")

    # Load data
    anthropic, onet_tasks, onet_occs, job_zones, education = load_data()

    # Extract Anthropic tasks
    task_data = extract_anthropic_tasks(anthropic)

    # Exact matching
    exact_matched, unmatched, onet_tasks = exact_match(task_data, onet_tasks)

    # Fuzzy matching
    fuzzy_matched = fuzzy_match(unmatched, onet_tasks)

    # Combine matches
    all_matched = pd.concat([exact_matched, fuzzy_matched], ignore_index=True)

    # Enrich with O*NET data
    enriched = enrich_with_onet(all_matched, onet_occs, job_zones, education)

    # Save outputs
    final, unmatched_final = save_outputs(enriched, task_data, PROCESSED_DIR)

    # Print summary
    print_summary(final, task_data, unmatched_final)

    print("\n" + "="*60)
    print("Done!")
    print("="*60)


if __name__ == '__main__':
    main()
