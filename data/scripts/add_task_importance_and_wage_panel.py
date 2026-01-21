"""
Add O*NET Task Importance and Build Wage Panel
===============================================

This script:
1. Adds O*NET task importance weights to the crosswalk
2. Creates a wage panel from BLS OES data (2022-2024)

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
ONET_DIR = DATA_DIR / "onet" / "db_30_1_excel"
BLS_DIR = DATA_DIR / "bls_oes"
PROCESSED_DIR = DATA_DIR / "processed"

# Input files
CROSSWALK_FILE = PROCESSED_DIR / "master_task_crosswalk_with_wages.csv"
TASK_RATINGS_FILE = ONET_DIR / "Task Ratings.xlsx"
BLS_FILES = {
    2022: BLS_DIR / "national_M2022_dl.xlsx",
    2023: BLS_DIR / "national_M2023_dl.xlsx",
    2024: BLS_DIR / "national_M2024_dl.xlsx"
}

# Output files
CROSSWALK_WITH_IMPORTANCE = PROCESSED_DIR / "master_task_crosswalk_with_importance.csv"
WAGE_PANEL_FILE = PROCESSED_DIR / "wage_panel_2022_2024.csv"

print("=" * 80)
print("ADDING TASK IMPORTANCE AND BUILDING WAGE PANEL")
print("=" * 80)

# =============================================================================
# STEP 1: Load O*NET Task Importance
# =============================================================================
print("\nSTEP 1: Loading O*NET task importance ratings...")

task_ratings = pd.read_excel(TASK_RATINGS_FILE)
print(f"  Loaded {len(task_ratings):,} task ratings")

# Filter for Importance scale only
importance = task_ratings[task_ratings['Scale ID'] == 'IM'].copy()
print(f"  Filtered to {len(importance):,} importance ratings")

# Keep relevant columns
importance = importance[[
    'O*NET-SOC Code',
    'Task ID',
    'Data Value'
]].rename(columns={
    'O*NET-SOC Code': 'onet_soc_code',
    'Task ID': 'onet_task_id',
    'Data Value': 'task_importance'
})

print(f"  Importance range: {importance['task_importance'].min():.1f} to {importance['task_importance'].max():.1f}")
print(f"  Mean importance: {importance['task_importance'].mean():.1f}")

# =============================================================================
# STEP 2: Merge Task Importance into Crosswalk
# =============================================================================
print("\nSTEP 2: Merging task importance into crosswalk...")

crosswalk = pd.read_csv(CROSSWALK_FILE)
print(f"  Original crosswalk: {len(crosswalk):,} rows")

# Merge on O*NET-SOC code and Task ID
crosswalk_with_importance = crosswalk.merge(
    importance,
    on=['onet_soc_code', 'onet_task_id'],
    how='left'
)

# Check merge success
matched = crosswalk_with_importance['task_importance'].notna().sum()
print(f"  Matched importance for {matched:,} rows ({100*matched/len(crosswalk):.1f}%)")

# For unmatched: fill with mean importance (neutral weight)
mean_importance = importance['task_importance'].mean()
crosswalk_with_importance['task_importance'] = crosswalk_with_importance['task_importance'].fillna(mean_importance)

print(f"  Filled {len(crosswalk) - matched:,} missing values with mean ({mean_importance:.1f})")

# Save
crosswalk_with_importance.to_csv(CROSSWALK_WITH_IMPORTANCE, index=False)
print(f"\n✓ Saved crosswalk with importance to: {CROSSWALK_WITH_IMPORTANCE}")

# =============================================================================
# STEP 3: Build Wage Panel from BLS OES Data
# =============================================================================
print("\nSTEP 3: Building wage panel from BLS OES data...")

wage_panel_list = []

for year, file_path in BLS_FILES.items():
    print(f"\n  Processing {year}...")

    df = pd.read_excel(file_path)
    print(f"    Loaded {len(df):,} occupations")

    # Keep national cross-industry estimates only
    df_nat = df[
        (df['AREA'] == 99) &  # National
        (df['NAICS'] == 0) &  # Cross-industry
        (df['OCC_CODE'] != '00-0000')  # Exclude "All Occupations" total
    ].copy()

    print(f"    Filtered to {len(df_nat):,} national cross-industry occupations")

    # Keep relevant columns
    df_nat = df_nat[[
        'OCC_CODE',
        'OCC_TITLE',
        'TOT_EMP',
        'A_MEAN',
        'A_MEDIAN',
        'H_MEAN'
    ]].rename(columns={
        'OCC_CODE': 'soc_code',
        'OCC_TITLE': 'occ_title',
        'TOT_EMP': 'employment',
        'A_MEAN': 'wage_annual_mean',
        'A_MEDIAN': 'wage_annual_median',
        'H_MEAN': 'wage_hourly_mean'
    })

    df_nat['year'] = year

    # Convert wage columns to numeric (handles both "#" and actual NaNs)
    wage_cols = ['wage_annual_mean', 'wage_annual_median', 'wage_hourly_mean', 'employment']
    for col in wage_cols:
        df_nat[col] = pd.to_numeric(df_nat[col], errors='coerce')

    # Drop rows with missing wages
    before = len(df_nat)
    df_nat = df_nat.dropna(subset=['wage_annual_mean', 'employment'])
    after = len(df_nat)
    if before > after:
        print(f"    Dropped {before - after} rows with missing wages/employment")

    wage_panel_list.append(df_nat)

# Concatenate all years
wage_panel = pd.concat(wage_panel_list, ignore_index=True)

print(f"\n  Combined panel shape: {len(wage_panel):,} rows × {len(wage_panel.columns)} columns")
print(f"  Years: {wage_panel['year'].unique()}")
print(f"  Unique occupations: {wage_panel['soc_code'].nunique():,}")

# Save
wage_panel.to_csv(WAGE_PANEL_FILE, index=False)
print(f"\n✓ Saved wage panel to: {WAGE_PANEL_FILE}")

# =============================================================================
# STEP 4: Summary Statistics
# =============================================================================
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print("\nTask Importance Distribution:")
print(crosswalk_with_importance['task_importance'].describe())

print("\nWage Panel Summary:")
for year in sorted(wage_panel['year'].unique()):
    year_data = wage_panel[wage_panel['year'] == year]
    print(f"\n  {year}:")
    print(f"    Occupations: {len(year_data):,}")
    print(f"    Mean wage: ${year_data['wage_annual_mean'].mean():,.0f}")
    print(f"    Median wage: ${year_data['wage_annual_median'].mean():,.0f}")
    print(f"    Total employment: {year_data['employment'].sum():,.0f}")

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)
print(f"\nOutputs:")
print(f"  1. {CROSSWALK_WITH_IMPORTANCE}")
print(f"  2. {WAGE_PANEL_FILE}")
