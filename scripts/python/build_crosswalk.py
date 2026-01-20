"""
Build Anthropic API Task → O*NET Crosswalk
===========================================

Links Anthropic Claude API task descriptions to O*NET occupational codes via:
1. Text normalization (lowercase, remove punctuation)
2. Exact string matching
3. Fuzzy matching (Levenshtein, threshold >= 85)
4. Enrichment with O*NET occupation attributes

AMBIGUOUS TASK HANDLING (v2):
Because O*NET task statements can be shared across multiple occupations, a subset
of Anthropic task strings maps to multiple SOCs. We treat these mappings as
ambiguous and allocate usage across candidate occupations using a conservative
equal-split rule (main specification). Employment-weighted allocation is provided
as a robustness check.

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import pandas as pd
from rapidfuzz import fuzz, process
import re
import os

# --- CONFIGURATION ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
AUDIT_DIR = os.path.join(DATA_DIR, 'audit')
ANTHROPIC_DATA = os.path.join(ROOT_DIR, '..', 'anthropic-econ-critique', 'data',
                               'release_2026_01_15', 'data', 'intermediate',
                               'aei_raw_1p_api_2025-11-13_to_2025-11-20.csv')
ONET_DIR = os.path.join(RAW_DIR, 'db_29_1_text')
BLS_DIR = os.path.join(DATA_DIR, 'BLS')
FUZZY_THRESHOLD = 85


def normalize_text(text):
    """Normalize text: lowercase, remove punctuation, collapse whitespace."""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def load_data():
    """Load Anthropic API data and O*NET reference files."""
    anthropic = pd.read_csv(ANTHROPIC_DATA)
    onet_tasks = pd.read_csv(os.path.join(ONET_DIR, 'Task Statements.txt'), sep='\t')
    onet_occs = pd.read_csv(os.path.join(ONET_DIR, 'Occupation Data.txt'), sep='\t')
    job_zones = pd.read_csv(os.path.join(ONET_DIR, 'Job Zones.txt'), sep='\t')
    education = pd.read_csv(os.path.join(ONET_DIR, 'Education, Training, and Experience.txt'), sep='\t')
    return anthropic, onet_tasks, onet_occs, job_zones, education


def extract_anthropic_tasks(anthropic):
    """Filter to O*NET task facet and extract task descriptions with API counts."""
    task_data = anthropic[
        (anthropic['facet'] == 'onet_task') &
        (anthropic['variable'] == 'onet_task_count')
    ][['cluster_name', 'value']].copy()
    task_data.columns = ['anthropic_task', 'api_count']

    # Exclude placeholder categories
    task_data = task_data[~task_data['anthropic_task'].str.lower().isin(['not_classified', 'none'])]
    task_data['task_norm'] = task_data['anthropic_task'].apply(normalize_text)
    return task_data


def analyze_onet_duplicates(onet_tasks):
    """
    Identify O*NET task statements that appear in multiple occupations.
    Returns lookup of task_norm -> list of (SOC, Task ID, Task, Task Type).
    """
    onet_tasks['task_norm'] = onet_tasks['Task'].apply(normalize_text)

    # Group by normalized text, collect all SOC codes
    task_to_socs = onet_tasks.groupby('task_norm').apply(
        lambda g: g[['O*NET-SOC Code', 'Task ID', 'Task', 'Task Type']].to_dict('records')
    ).to_dict()

    # Count SOCs per task
    soc_counts = {k: len(v) for k, v in task_to_socs.items()}

    return task_to_socs, soc_counts


def exact_match(task_data, onet_tasks, task_to_socs, soc_counts):
    """
    Match normalized Anthropic tasks to O*NET tasks via exact string comparison.

    IMPORTANT: Handles ambiguous tasks (same text -> multiple SOCs) by creating
    multiple rows with equal-split usage weights.
    """
    matched_rows = []
    unmatched_rows = []
    ambiguous_group_id = 0

    for _, row in task_data.iterrows():
        task_norm = row['task_norm']

        if task_norm in task_to_socs:
            soc_list = task_to_socs[task_norm]
            n_socs = len(soc_list)
            is_ambiguous = n_socs > 1

            if is_ambiguous:
                ambiguous_group_id += 1

            for soc_info in soc_list:
                matched_rows.append({
                    'anthropic_task': row['anthropic_task'],
                    'api_count_original': row['api_count'],
                    'api_count': row['api_count'] / n_socs,  # Equal split
                    'split_weight': 1.0 / n_socs,
                    'n_candidate_socs': n_socs,
                    'is_ambiguous': is_ambiguous,
                    'ambiguous_group_id': ambiguous_group_id if is_ambiguous else None,
                    'task_norm': task_norm,
                    'O*NET-SOC Code': soc_info['O*NET-SOC Code'],
                    'Task ID': soc_info['Task ID'],
                    'Task': soc_info['Task'],
                    'Task Type': soc_info['Task Type'],
                    'match_method': 'exact',
                    'match_score': 100.0
                })
        else:
            unmatched_rows.append({
                'anthropic_task': row['anthropic_task'],
                'api_count': row['api_count'],
                'task_norm': task_norm
            })

    matched = pd.DataFrame(matched_rows)
    unmatched = pd.DataFrame(unmatched_rows)

    return matched, unmatched


def fuzzy_match(unmatched, onet_tasks, task_to_socs, threshold=FUZZY_THRESHOLD):
    """
    Match remaining tasks using Levenshtein similarity (rapidfuzz).

    IMPORTANT: Handles ambiguous tasks by creating multiple rows with equal-split weights.
    """
    onet_choices = list(task_to_socs.keys())

    fuzzy_rows = []
    still_unmatched = []
    ambiguous_group_id = 10000  # Offset to distinguish from exact match groups

    for _, row in unmatched.iterrows():
        result = process.extractOne(row['task_norm'], onet_choices, scorer=fuzz.ratio)

        if result and result[1] >= threshold:
            match_text, score, _ = result
            soc_list = task_to_socs[match_text]
            n_socs = len(soc_list)
            is_ambiguous = n_socs > 1

            if is_ambiguous:
                ambiguous_group_id += 1

            for soc_info in soc_list:
                fuzzy_rows.append({
                    'anthropic_task': row['anthropic_task'],
                    'api_count_original': row['api_count'],
                    'api_count': row['api_count'] / n_socs,  # Equal split
                    'split_weight': 1.0 / n_socs,
                    'n_candidate_socs': n_socs,
                    'is_ambiguous': is_ambiguous,
                    'ambiguous_group_id': ambiguous_group_id if is_ambiguous else None,
                    'task_norm': row['task_norm'],
                    'matched_onet_norm': match_text,
                    'O*NET-SOC Code': soc_info['O*NET-SOC Code'],
                    'Task ID': soc_info['Task ID'],
                    'Task': soc_info['Task'],
                    'Task Type': soc_info['Task Type'],
                    'match_method': 'fuzzy',
                    'match_score': score
                })
        else:
            still_unmatched.append(row.to_dict())

    return pd.DataFrame(fuzzy_rows), pd.DataFrame(still_unmatched)


def enrich_with_onet(matched, onet_occs, job_zones, education):
    """Add occupation titles, job zones, and typical education from O*NET."""
    # Occupation titles
    matched = matched.merge(
        onet_occs[['O*NET-SOC Code', 'Title', 'Description']],
        on='O*NET-SOC Code', how='left'
    )

    # Job zones (1-5 education/preparation scale)
    jz_clean = job_zones[['O*NET-SOC Code', 'Job Zone']].drop_duplicates()
    matched = matched.merge(jz_clean, on='O*NET-SOC Code', how='left')

    # Typical education level
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


def generate_audit_outputs(matched, unmatched, task_data, onet_tasks, task_to_socs, soc_counts, output_dir):
    """
    Generate audit CSV files for transparency and reproducibility.

    Outputs:
    1. onet_task_text_duplicates.csv - O*NET tasks shared across multiple SOCs
    2. anthropic_tasks_ambiguous_matches.csv - Anthropic tasks with ambiguous mappings
    3. exposure_accounting_check.csv - Verify usage totals are conserved
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. O*NET task text duplicates
    dup_rows = []
    for task_norm, soc_list in task_to_socs.items():
        if len(soc_list) > 1:
            soc_codes = [s['O*NET-SOC Code'] for s in soc_list]
            dup_rows.append({
                'normalized_task_text': task_norm,
                'original_task_text': soc_list[0]['Task'],
                'n_socs': len(soc_list),
                'soc_codes': '; '.join(soc_codes)
            })

    dup_df = pd.DataFrame(dup_rows).sort_values('n_socs', ascending=False)
    dup_df.to_csv(os.path.join(output_dir, 'onet_task_text_duplicates.csv'), index=False)

    # 2. Anthropic tasks with ambiguous matches
    if len(matched) > 0:
        ambig = matched[matched['is_ambiguous'] == True].copy()
        if len(ambig) > 0:
            ambig_summary = ambig.groupby('anthropic_task').agg({
                'api_count_original': 'first',
                'n_candidate_socs': 'first',
                'O*NET-SOC Code': lambda x: '; '.join(x.unique()),
                'Title': lambda x: '; '.join(x.dropna().unique()),
                'match_method': 'first',
                'match_score': 'first'
            }).reset_index()
            ambig_summary.columns = [
                'anthropic_task_description', 'api_usage_count_original',
                'n_candidate_socs', 'candidate_soc_codes', 'candidate_titles',
                'match_method', 'match_score'
            ]
            ambig_summary = ambig_summary.sort_values('api_usage_count_original', ascending=False)
            ambig_summary.to_csv(os.path.join(output_dir, 'anthropic_tasks_ambiguous_matches.csv'), index=False)

    # 3. Exposure accounting check
    total_anthropic_usage = task_data['api_count'].sum()

    # Get unique matched usage (sum original usage for each unique Anthropic task)
    if len(matched) > 0:
        unique_task_usage = matched.groupby('anthropic_task')['api_count_original'].first().sum()
        matched_usage_split = matched['api_count'].sum()
    else:
        unique_task_usage = 0
        matched_usage_split = 0

    unmatched_usage = unmatched['api_count'].sum() if len(unmatched) > 0 else 0

    # Unique matched tasks (before split)
    n_unique_matched = matched['anthropic_task'].nunique() if len(matched) > 0 else 0
    n_ambiguous_tasks = matched[matched['is_ambiguous'] == True]['anthropic_task'].nunique() if len(matched) > 0 else 0

    accounting = pd.DataFrame({
        'Stage': [
            'Total Anthropic API usage (filtered)',
            'Matched usage (unique tasks)',
            'Matched usage (after equal split)',
            'Unmatched usage',
            'Matched + Unmatched (should equal Total)',
            'Unique matched task descriptions',
            'Ambiguous task descriptions (multi-SOC)',
            'Total rows in crosswalk (after expansion)',
            'Conservation check (split total = unique matched)'
        ],
        'Value': [
            total_anthropic_usage,
            unique_task_usage,
            matched_usage_split,
            unmatched_usage,
            unique_task_usage + unmatched_usage,
            n_unique_matched,
            n_ambiguous_tasks,
            len(matched),
            'PASS' if abs(matched_usage_split - unique_task_usage) < 1 else 'FAIL'
        ],
        'Percent_of_Total': [
            '100.0%',
            f'{100 * unique_task_usage / total_anthropic_usage:.2f}%' if total_anthropic_usage > 0 else 'N/A',
            f'{100 * matched_usage_split / total_anthropic_usage:.2f}%' if total_anthropic_usage > 0 else 'N/A',
            f'{100 * unmatched_usage / total_anthropic_usage:.2f}%' if total_anthropic_usage > 0 else 'N/A',
            f'{100 * (unique_task_usage + unmatched_usage) / total_anthropic_usage:.2f}%' if total_anthropic_usage > 0 else 'N/A',
            f'{100 * n_unique_matched / len(task_data):.2f}%' if len(task_data) > 0 else 'N/A',
            f'{100 * n_ambiguous_tasks / n_unique_matched:.2f}%' if n_unique_matched > 0 else 'N/A',
            'N/A',
            'N/A'
        ]
    })
    accounting.to_csv(os.path.join(output_dir, 'exposure_accounting_check.csv'), index=False)

    return dup_df, accounting


def merge_bls_wages(matched, bls_dir):
    """
    Merge BLS OEWS wage and employment data onto the crosswalk.

    BLS uses 6-digit SOC codes; O*NET uses 8-digit (with .XX suffix).
    Join on truncated 6-digit code.
    """
    bls_file = os.path.join(bls_dir, 'national_wages_2024.csv')

    if not os.path.exists(bls_file):
        # Try the OEWS directory
        oews_dir = os.path.join(bls_dir, 'oesm24all')
        xlsx_file = os.path.join(oews_dir, 'all_data_M_2024.xlsx')
        if os.path.exists(xlsx_file):
            print(f"  Loading BLS data from {xlsx_file}...")
            bls = pd.read_excel(xlsx_file)
        else:
            print(f"  Warning: BLS data not found. Skipping wage merge.")
            return matched
    else:
        print(f"  Loading BLS data from {bls_file}...")
        bls = pd.read_csv(bls_file)

    # Filter to national, cross-industry, detailed occupations
    if 'AREA' in bls.columns:
        bls = bls[
            (bls['AREA'] == 99) &
            (bls['NAICS'] == '000000') &
            (bls['O_GROUP'] == 'detailed')
        ]

    # Create 6-digit SOC for joining
    matched['soc_6digit'] = matched['O*NET-SOC Code'].str.split('.').str[0]

    # Select relevant BLS columns
    bls_cols = ['OCC_CODE', 'OCC_TITLE', 'TOT_EMP', 'H_MEAN', 'A_MEAN', 'H_MEDIAN', 'A_MEDIAN',
                'H_PCT10', 'H_PCT25', 'H_PCT75', 'H_PCT90', 'A_PCT10', 'A_PCT25', 'A_PCT75', 'A_PCT90']
    bls_cols = [c for c in bls_cols if c in bls.columns]

    bls_subset = bls[bls_cols].drop_duplicates(subset=['OCC_CODE'])

    # Convert wage columns to numeric
    for col in bls_subset.columns:
        if col not in ['OCC_CODE', 'OCC_TITLE']:
            bls_subset[col] = pd.to_numeric(bls_subset[col], errors='coerce')

    # Merge
    merged = matched.merge(bls_subset, left_on='soc_6digit', right_on='OCC_CODE', how='left')

    n_matched = merged['OCC_CODE'].notna().sum()
    n_total = len(merged)
    print(f"  BLS wage match: {n_matched}/{n_total} rows ({100*n_matched/n_total:.1f}%)")

    return merged


def save_outputs(matched, task_data, unmatched, output_dir):
    """Save crosswalk and unmatched tasks to CSV."""
    # Ensure matched_onet_norm column exists (may be missing for exact matches)
    if 'matched_onet_norm' not in matched.columns:
        matched['matched_onet_norm'] = None

    final = matched[[
        'anthropic_task', 'api_count_original', 'api_count', 'split_weight',
        'n_candidate_socs', 'is_ambiguous', 'ambiguous_group_id',
        'O*NET-SOC Code', 'Task ID', 'Task', 'Task Type',
        'Title', 'Description',
        'match_method', 'match_score',
        'Job Zone', 'typical_education', 'typical_education_pct'
    ]].copy()

    final.columns = [
        'anthropic_task_description', 'api_usage_count_original', 'api_usage_count', 'split_weight',
        'n_candidate_socs', 'is_ambiguous', 'ambiguous_group_id',
        'onet_soc_code', 'onet_task_id', 'onet_task_description', 'onet_task_type',
        'onet_occupation_title', 'onet_occupation_description',
        'match_method', 'match_score',
        'job_zone', 'typical_education', 'typical_education_pct'
    ]

    final = final.sort_values('api_usage_count_original', ascending=False)
    final.to_csv(os.path.join(output_dir, 'master_task_crosswalk.csv'), index=False)

    # Unmatched tasks
    if len(unmatched) > 0:
        unmatched[['anthropic_task', 'api_count']].to_csv(
            os.path.join(output_dir, 'unmatched_tasks.csv'), index=False
        )

    return final


def main():
    """Execute crosswalk build pipeline."""
    # Create output directories
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(AUDIT_DIR, exist_ok=True)

    # Load data
    print("Loading data...")
    anthropic, onet_tasks, onet_occs, job_zones, education = load_data()

    # Analyze O*NET duplicates
    print("Analyzing O*NET task duplicates...")
    task_to_socs, soc_counts = analyze_onet_duplicates(onet_tasks)
    n_duplicated = sum(1 for c in soc_counts.values() if c > 1)
    print(f"  - {len(task_to_socs):,} unique normalized O*NET tasks")
    print(f"  - {n_duplicated:,} tasks appear in multiple SOCs ({100*n_duplicated/len(task_to_socs):.1f}%)")

    # Extract and match tasks
    print("Extracting Anthropic tasks...")
    task_data = extract_anthropic_tasks(anthropic)
    print(f"  - {len(task_data):,} unique task descriptions")
    print(f"  - {task_data['api_count'].sum():,.0f} total API usage")

    print("Performing exact matching...")
    exact_matched, unmatched, = exact_match(task_data, onet_tasks, task_to_socs, soc_counts)
    print(f"  - {exact_matched['anthropic_task'].nunique():,} tasks matched exactly")
    print(f"  - {len(unmatched):,} tasks unmatched")

    print("Performing fuzzy matching...")
    fuzzy_matched, still_unmatched = fuzzy_match(unmatched, onet_tasks, task_to_socs)
    print(f"  - {fuzzy_matched['anthropic_task'].nunique():,} tasks matched via fuzzy")
    print(f"  - {len(still_unmatched):,} tasks still unmatched")

    # Combine and enrich
    print("Enriching with O*NET attributes...")
    all_matched = pd.concat([exact_matched, fuzzy_matched], ignore_index=True)
    enriched = enrich_with_onet(all_matched, onet_occs, job_zones, education)

    # Summary stats
    n_ambiguous = enriched[enriched['is_ambiguous'] == True]['anthropic_task'].nunique()
    ambig_usage = enriched[enriched['is_ambiguous'] == True]['api_count_original'].drop_duplicates().sum()
    total_matched_usage = enriched['api_count_original'].drop_duplicates().sum()
    print(f"\nAmbiguity summary:")
    print(f"  - {n_ambiguous:,} tasks map to multiple SOCs ({100*n_ambiguous/enriched['anthropic_task'].nunique():.1f}%)")
    print(f"  - {ambig_usage:,.0f} API usage in ambiguous tasks ({100*ambig_usage/total_matched_usage:.1f}%)")

    # Generate audit outputs
    print("\nGenerating audit outputs...")
    generate_audit_outputs(enriched, still_unmatched, task_data, onet_tasks, task_to_socs, soc_counts, AUDIT_DIR)

    # Save main outputs
    print("Saving crosswalk...")
    save_outputs(enriched, task_data, still_unmatched, PROCESSED_DIR)

    # Merge BLS wages
    print("\nMerging BLS wage data...")
    with_wages = merge_bls_wages(enriched, BLS_DIR)

    # Rename columns for estimate_models.py compatibility
    rename_map = {
        'anthropic_task': 'anthropic_task_description',
        'api_count_original': 'api_usage_count_original',
        'api_count': 'api_usage_count',
        'O*NET-SOC Code': 'onet_soc_code',
        'Task ID': 'onet_task_id',
        'Task': 'onet_task_description',
        'Task Type': 'onet_task_type',
        'Title': 'onet_occupation_title',
        'Description': 'onet_occupation_description',
        'Job Zone': 'job_zone'
    }
    with_wages = with_wages.rename(columns=rename_map)

    # Save crosswalk with wages
    wages_output = os.path.join(PROCESSED_DIR, 'master_task_crosswalk_with_wages.csv')
    with_wages.to_csv(wages_output, index=False)
    print(f"  Saved: {wages_output}")

    print(f"\nDone! Outputs saved to:")
    print(f"  - {PROCESSED_DIR}/master_task_crosswalk.csv")
    print(f"  - {PROCESSED_DIR}/master_task_crosswalk_with_wages.csv")
    print(f"  - {PROCESSED_DIR}/unmatched_tasks.csv")
    print(f"  - {AUDIT_DIR}/onet_task_text_duplicates.csv")
    print(f"  - {AUDIT_DIR}/anthropic_tasks_ambiguous_matches.csv")
    print(f"  - {AUDIT_DIR}/exposure_accounting_check.csv")


if __name__ == '__main__':
    main()
