"""
Claude API Usage-Wage Intensity Regressions (O-ring interpretation)
====================================================================

This script estimates the relationship between Claude API usage intensity and wages
at the SOC-occupation level, using master_task_crosswalk_with_wages.csv.

IMPORTANT CONCEPTUAL NOTE:
--------------------------
This script estimates **associations** between allocated Claude usage and wages.
It does NOT estimate structural parameters of an O-ring production function.

The positive usage-wage correlation can be *interpreted* through Gans & Goldfarb's
(2025) O-ring framework (tasks as quality complements, partial automation raises
bottleneck value), but we are not identifying causal mechanisms or complementarity
parameters. See INTERPRETATION.md for theoretical discussion.

Following ChatGPT feedback corrections:
- Use GLM Poisson (quasi-likelihood) instead of discrete Poisson with rounding
- Fix split-weight verification logic
- Add data quality guardrails (employment>0, wage>0)
- Clarify task-level model interpretation
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set up paths
DATA_PATH = Path.home() / "anthropic-onet-crosswalk" / "data" / "processed" / "master_task_crosswalk_with_wages.csv"
OUTPUT_DIR = Path.home() / "anthropic-onet-crosswalk" / "models" / "oring_automation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configure display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
sns.set_style("whitegrid")

print("="*80)
print("CLAUDE API USAGE-WAGE INTENSITY REGRESSIONS")
print("(O-ring complementarity interpretation)")
print("="*80)
print()

# ================================
# STEP 1: LOAD AND INSPECT DATA
# ================================
print("STEP 1: Loading data...")
df = pd.read_csv(DATA_PATH)

print(f"\nDataset dimensions: {df.shape[0]:,} rows × {df.shape[1]} columns")

print(f"\nAmbiguous mapping stats:")
print(f"  Total rows: {len(df):,}")
print(f"  Ambiguous: {df['is_ambiguous'].sum():,} ({100*df['is_ambiguous'].mean():.1f}%)")
print(f"  Non-ambiguous: {(~df['is_ambiguous']).sum():,}")

# CORRECTED SPLIT-WEIGHT VERIFICATION
print(f"\n" + "-"*80)
print("CORRECTED: Verifying split-weight logic")
print("-"*80)
print("For ambiguous tasks, sum(api_usage_count) across split rows should equal")
print("the FIRST (unique) value of api_usage_count_original for that task.")

ambig_check = df[df['is_ambiguous']].groupby('anthropic_task_description').agg(
    split_sum=('api_usage_count', 'sum'),
    original=('api_usage_count_original', 'first'),  # NOT sum!
    n_rows=('api_usage_count', 'count')
)
ambig_check['ratio'] = ambig_check['split_sum'] / ambig_check['original']
print(f"\nAmbiguous tasks verification:")
print(f"  Mean ratio (split_sum / original): {ambig_check['ratio'].mean():.4f} (should be ~1.0)")
print(f"  Min ratio: {ambig_check['ratio'].min():.4f}")
print(f"  Max ratio: {ambig_check['ratio'].max():.4f}")
print(f"  Std dev: {ambig_check['ratio'].std():.4f}")

if abs(ambig_check['ratio'].mean() - 1.0) > 0.01:
    print(f"\n⚠️  WARNING: Split weights don't sum correctly!")
else:
    print(f"\n✓ Split weights verified: mass is conserved")

# ================================
# STEP 2: DATA PREPARATION WITH GUARDRAILS
# ================================
print("\n" + "="*80)
print("STEP 2: Data preparation with quality guardrails")
print("="*80)

df_clean = df.copy()
initial_n = len(df_clean)

# Drop if missing critical fields
df_clean = df_clean.dropna(subset=['soc_6digit', 'TOT_EMP', 'api_usage_count'])
print(f"\nAfter dropping missing soc_6digit/TOT_EMP/api_usage_count: {len(df_clean):,} rows")

# Wage imputation (prefer A_MEAN, use H_MEAN * 2080 as backup)
df_clean['wage_annual'] = df_clean['A_MEAN'].fillna(df_clean['H_MEAN'] * 2080)
df_clean['wage_hourly'] = df_clean['H_MEAN'].fillna(df_clean['A_MEAN'] / 2080)

# GUARDRAIL: Drop rows with non-positive employment or wages (would break logs)
df_clean = df_clean[
    (df_clean['TOT_EMP'] > 0) &
    (df_clean['wage_annual'] > 0) &
    (df_clean['wage_annual'].notna())
]
print(f"After requiring TOT_EMP > 0 and wage_annual > 0: {len(df_clean):,} rows ({len(df_clean)/initial_n*100:.1f}% retained)")

# CORRECTED: Handle onet_task_type mapping
print(f"\nonet_task_type value counts:")
print(df_clean['onet_task_type'].value_counts(dropna=False))

# Map to binary (handle potential case variations)
df_clean['is_core_task'] = df_clean['onet_task_type'].str.lower().str.contains('core', na=False).astype(int)
print(f"\nCore task indicator:")
print(f"  is_core_task = 1: {df_clean['is_core_task'].sum():,} ({100*df_clean['is_core_task'].mean():.1f}%)")
print(f"  is_core_task = 0: {(df_clean['is_core_task']==0).sum():,}")

# ================================
# SETUP A: SOC-LEVEL AGGREGATION
# ================================
print("\n" + "="*80)
print("SETUP A: SOC-LEVEL MODEL")
print("="*80)
print("\nAggregating to SOC level...")

soc_agg = df_clean.groupby('soc_6digit').agg({
    'api_usage_count': 'sum',  # U_s = total Claude usage mass
    'TOT_EMP': 'first',  # E_s = employment
    'wage_annual': 'first',  # W_s = annual mean wage
    'wage_hourly': 'first',
    'OCC_TITLE': 'first',
    'is_core_task': 'mean',  # share of core tasks
    'match_score': 'mean',
    'is_ambiguous': 'mean'
}).reset_index()

soc_agg.columns = ['soc_6digit', 'usage_total', 'employment', 'wage_annual', 'wage_hourly',
                   'occ_title', 'share_core', 'avg_match_score', 'share_ambiguous']

# Usage intensity
soc_agg['usage_per_worker'] = soc_agg['usage_total'] / soc_agg['employment']

# GUARDRAIL: Verify all positive before logging
assert (soc_agg['employment'] > 0).all(), "Some SOCs have employment ≤ 0!"
assert (soc_agg['wage_annual'] > 0).all(), "Some SOCs have wage ≤ 0!"

# Log transformations
soc_agg['log_wage'] = np.log(soc_agg['wage_annual'])
soc_agg['log_employment'] = np.log(soc_agg['employment'])
soc_agg['log_usage_intensity'] = np.log(soc_agg['usage_per_worker'] + 1e-6)  # small constant for zeros

print(f"\nSOC-level dataset:")
print(f"  Number of unique SOCs: {len(soc_agg):,}")
print(f"  SOCs with zero usage: {(soc_agg['usage_total'] == 0).sum():,}")
print(f"  Mean usage per SOC: {soc_agg['usage_total'].mean():.1f}")
print(f"  Mean wage: ${soc_agg['wage_annual'].mean():,.0f}")

print(f"\nDescriptive statistics:")
print(soc_agg[['usage_total', 'usage_per_worker', 'employment', 'wage_annual', 'share_core']].describe())

# ================================
# MODEL A1: GLM POISSON (QUASI-LIKELIHOOD)
# ================================
print("\n" + "-"*80)
print("MODEL A1: GLM Poisson (quasi-likelihood, NO ROUNDING)")
print("-"*80)
print("\nUsing GLM Poisson with quasi-likelihood for fractional usage outcomes.")
print("This avoids measurement error from rounding split-weighted usage counts.")

poisson_data = soc_agg[['usage_total', 'log_wage', 'log_employment', 'share_core', 'avg_match_score']].dropna()

print(f"\nPoisson dataset: {len(poisson_data):,} SOCs")
print(f"Usage range: {poisson_data['usage_total'].min():.2f} to {poisson_data['usage_total'].max():.2f}")
print(f"Note: Many are fractional due to split weights (no rounding applied)")

# GLM Poisson with offset (quasi-likelihood)
glm_poisson = sm.GLM(
    endog=poisson_data['usage_total'],
    exog=sm.add_constant(poisson_data[['log_wage', 'share_core', 'avg_match_score']]),
    family=sm.families.Poisson(),
    offset=poisson_data['log_employment']
).fit(cov_type='HC3')

print("\n" + glm_poisson.summary().as_text())

# ================================
# MODEL A2: LOG-LINEAR OLS (PRIMARY)
# ================================
print("\n" + "-"*80)
print("MODEL A2: Log-linear OLS (log(usage_per_worker + c) ~ log(wage))")
print("-"*80)
print("\nTreating usage_per_worker as continuous outcome.")

ols_data = soc_agg[['log_usage_intensity', 'log_wage', 'share_core', 'avg_match_score']].dropna()

ols_model = OLS(
    endog=ols_data['log_usage_intensity'],
    exog=sm.add_constant(ols_data[['log_wage', 'share_core', 'avg_match_score']])
).fit(cov_type='HC3')

print("\n" + ols_model.summary().as_text())

# ================================
# SETUP B: TASK-WITHIN-SOC MODEL
# ================================
print("\n" + "="*80)
print("SETUP B: TASK-WITHIN-SOC MODEL")
print("="*80)
print("\nIMPORTANT: log_wage is SOC-level (doesn't vary within SOC).")
print("Identifying variation for β(log_wage) is BETWEEN SOCs, not within.")
print("Clustering at SOC level is correct, but SOCs with more tasks get more weight")
print("unless we reweight rows by 1/(tasks per SOC).")

task_data = df_clean.copy()
task_data['log_usage_plus1'] = np.log(1 + task_data['api_usage_count'])
task_data['log_wage'] = np.log(task_data['wage_annual'])
task_data['is_ambiguous_num'] = task_data['is_ambiguous'].astype(int)

print(f"\nTask-level dataset:")
print(f"  Number of (SOC, task) observations: {len(task_data):,}")
print(f"  Number of unique SOCs: {task_data['soc_6digit'].nunique():,}")
print(f"  Mean tasks per SOC: {len(task_data) / task_data['soc_6digit'].nunique():.1f}")

# MODEL B1: Task-level with clustering
print("\n" + "-"*80)
print("MODEL B1: Task-level OLS with SOC clustering")
print("-"*80)

task_reg_data = task_data[['log_usage_plus1', 'log_wage', 'is_core_task', 'match_score', 'is_ambiguous_num', 'soc_6digit']].dropna()

task_model = OLS(
    endog=task_reg_data['log_usage_plus1'],
    exog=sm.add_constant(task_reg_data[['log_wage', 'is_core_task', 'match_score', 'is_ambiguous_num']])
).fit(cov_type='cluster', cov_kwds={'groups': task_reg_data['soc_6digit']})

print("\n" + task_model.summary().as_text())

# ================================
# SENSITIVITY: EXCLUDE AMBIGUOUS
# ================================
print("\n" + "="*80)
print("SENSITIVITY ANALYSIS: Excluding ambiguous mappings")
print("="*80)

# SOC-level without ambiguous
soc_agg_no_amb = df_clean[~df_clean['is_ambiguous']].groupby('soc_6digit').agg({
    'api_usage_count': 'sum',
    'TOT_EMP': 'first',
    'wage_annual': 'first',
    'is_core_task': 'mean',
    'match_score': 'mean'
}).reset_index()

soc_agg_no_amb['log_wage'] = np.log(soc_agg_no_amb['wage_annual'])
soc_agg_no_amb['log_employment'] = np.log(soc_agg_no_amb['TOT_EMP'])

print(f"\nSOCs in non-ambiguous sample: {len(soc_agg_no_amb):,}")

glm_poisson_no_amb = sm.GLM(
    endog=soc_agg_no_amb['api_usage_count'],
    exog=sm.add_constant(soc_agg_no_amb[['log_wage', 'is_core_task', 'match_score']].fillna(0)),
    family=sm.families.Poisson(),
    offset=soc_agg_no_amb['log_employment']
).fit(cov_type='HC3')

print("\nGLM Poisson (excluding ambiguous):")
print(glm_poisson_no_amb.summary().as_text())

# Task-level without ambiguous
task_no_amb = task_reg_data[task_reg_data['is_ambiguous_num'] == 0]
print(f"\nTask observations (non-ambiguous): {len(task_no_amb):,}")

task_model_no_amb = OLS(
    endog=task_no_amb['log_usage_plus1'],
    exog=sm.add_constant(task_no_amb[['log_wage', 'is_core_task', 'match_score']])
).fit(cov_type='cluster', cov_kwds={'groups': task_no_amb['soc_6digit']})

print("\nTask-level OLS (excluding ambiguous):")
print(task_model_no_amb.summary().as_text())

# ================================
# RESULTS SUMMARY
# ================================
print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80)

summary_results = pd.DataFrame({
    'Model': [
        'A1: GLM Poisson (full)',
        'A1: GLM Poisson (no amb)',
        'A2: Log-linear OLS',
        'B1: Task-level OLS (full)',
        'B1: Task-level OLS (no amb)'
    ],
    'Beta_log_wage': [
        glm_poisson.params['log_wage'],
        glm_poisson_no_amb.params['log_wage'],
        ols_model.params['log_wage'],
        task_model.params['log_wage'],
        task_model_no_amb.params['log_wage']
    ],
    'SE': [
        glm_poisson.bse['log_wage'],
        glm_poisson_no_amb.bse['log_wage'],
        ols_model.bse['log_wage'],
        task_model.bse['log_wage'],
        task_model_no_amb.bse['log_wage']
    ],
    'P_value': [
        glm_poisson.pvalues['log_wage'],
        glm_poisson_no_amb.pvalues['log_wage'],
        ols_model.pvalues['log_wage'],
        task_model.pvalues['log_wage'],
        task_model_no_amb.pvalues['log_wage']
    ],
    'N': [
        len(poisson_data),
        len(soc_agg_no_amb),
        len(ols_data),
        len(task_reg_data),
        len(task_no_amb)
    ]
})

summary_results['Significant'] = (summary_results['P_value'] < 0.05).map({True: '***', False: ''})
summary_results['Beta_formatted'] = summary_results.apply(
    lambda row: f"{row['Beta_log_wage']:.4f} ({row['SE']:.4f}){row['Significant']}", axis=1
)

print("\nCoefficient on log(wage):")
print(summary_results[['Model', 'Beta_formatted', 'N']].to_string(index=False))

print("\nINTERPRETATION:")
print("β > 0 and significant: Higher-wage occupations have higher Claude usage intensity per worker.")
print("This is consistent with O-ring complementarity (Gans & Goldfarb 2025):")
print("  - Claude automates routine components of high-skill jobs")
print("  - Workers reallocate time to high-value bottleneck tasks")
print("  - Usage scales with wage because automation complements, not substitutes")
print("\nBut this is ASSOCIATIONAL evidence, not structural estimation of O-ring parameters.")
print("See INTERPRETATION.md for full theoretical discussion.")

# Save results
summary_results.to_csv(OUTPUT_DIR / 'model_summary.csv', index=False)
soc_agg.to_csv(OUTPUT_DIR / 'soc_level_data.csv', index=False)

print(f"\n✓ Results saved to: {OUTPUT_DIR}")
print("\n" + "="*80)
print("ESTIMATION COMPLETE")
print("="*80)
