"""
O-Ring Automation Model Estimation
==================================

This script estimates two model specifications using master_task_crosswalk_with_wages.csv:
- SETUP A (SOC-level): Occupation-level Claude usage intensity vs wages (Poisson/NegBin with employment offset)
- SETUP B (Task-level): Task-within-SOC model with clustering

Following instructions from ChatGPT, implementing O-ring automation framework (Gans & Goldfarb 2025).

Key insight: Unlike standard task-based models (separable tasks), O-ring production assumes tasks are
quality complements (Y = ∏qs). When AI automates some tasks, workers reallocate fixed time to remaining
tasks, increasing quality on those bottleneck tasks → potentially INCREASING wages under partial automation.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.discrete.count_model import Poisson
from statsmodels.discrete.discrete_model import NegativeBinomial
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
print("O-RING AUTOMATION MODEL ESTIMATION")
print("="*80)
print()

# ================================
# STEP 1: LOAD AND INSPECT DATA
# ================================
print("STEP 1: Loading data...")
df = pd.read_csv(DATA_PATH)

print(f"\nDataset dimensions: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"\nKey columns present:")
for col in ['anthropic_task_description', 'api_usage_count_original', 'api_usage_count',
            'split_weight', 'n_candidate_socs', 'is_ambiguous', 'onet_soc_code', 'soc_6digit',
            'TOT_EMP', 'A_MEAN', 'H_MEAN', 'onet_task_type', 'match_score']:
    if col in df.columns:
        print(f"  ✓ {col}")
    else:
        print(f"  ✗ {col} (MISSING)")

print(f"\nAmbiguous mapping stats:")
print(f"  Total rows: {len(df):,}")
print(f"  Ambiguous: {df['is_ambiguous'].sum():,} ({100*df['is_ambiguous'].mean():.1f}%)")
print(f"  Non-ambiguous: {(~df['is_ambiguous']).sum():,}")

print(f"\nVerifying split weight logic (should sum to total original usage):")
# For ambiguous tasks, sum across split rows should equal original
# For non-ambiguous tasks, they should be equal
ambiguous_check = df[df['is_ambiguous']].groupby('anthropic_task_description')[['api_usage_count_original', 'api_usage_count']].sum()
ambiguous_check['ratio'] = ambiguous_check['api_usage_count'] / ambiguous_check['api_usage_count_original']
print(f"  Ambiguous tasks: mean ratio of split/original = {ambiguous_check['ratio'].mean():.3f}")
print(f"  (This shows whether splitting works correctly; should be ~1.0 per unique task)")

total_original = df['api_usage_count_original'].sum()
total_split = df['api_usage_count'].sum()
print(f"\n  WARNING: Sum across ALL rows (double-counts ambiguous originals):")
print(f"  Sum(api_usage_count_original): {total_original:,.0f}")
print(f"  Sum(api_usage_count): {total_split:,.1f}")
print(f"  (Difference expected due to ambiguous tasks appearing in multiple rows)")

# ================================
# STEP 2: DATA HYGIENE & PREPARATION
# ================================
print("\n" + "="*80)
print("STEP 2: Data preparation")
print("="*80)

# Check for missing values in key fields
print("\nMissing values in key fields:")
key_fields = ['soc_6digit', 'TOT_EMP', 'A_MEAN', 'H_MEAN', 'api_usage_count']
for field in key_fields:
    n_missing = df[field].isna().sum()
    print(f"  {field}: {n_missing:,} ({100*n_missing/len(df):.1f}%)")

# For SOC-level analysis, we'll use A_MEAN (annual mean wage) as primary wage measure
# Drop rows missing critical fields
df_clean = df.copy()
initial_n = len(df_clean)

# Drop if missing SOC code, employment, or API usage
df_clean = df_clean.dropna(subset=['soc_6digit', 'TOT_EMP', 'api_usage_count'])
print(f"\nAfter dropping rows with missing soc_6digit/TOT_EMP/api_usage_count: {len(df_clean):,} rows ({len(df_clean)/initial_n*100:.1f}% retained)")

# For wage analysis, prefer A_MEAN but can use H_MEAN * 2080 as backup
df_clean['wage_annual'] = df_clean['A_MEAN'].fillna(df_clean['H_MEAN'] * 2080)
df_clean['wage_hourly'] = df_clean['H_MEAN'].fillna(df_clean['A_MEAN'] / 2080)

n_missing_wage = df_clean['wage_annual'].isna().sum()
print(f"Rows still missing wage data after imputation: {n_missing_wage:,}")

# Drop rows still missing wage
df_clean = df_clean.dropna(subset=['wage_annual'])
print(f"After dropping rows with missing wages: {len(df_clean):,} rows ({len(df_clean)/initial_n*100:.1f}% retained)")

# Create indicator for core vs supplemental tasks
df_clean['is_core_task'] = (df_clean['onet_task_type'] == 'Core').astype(int)

# ================================
# SETUP A: SOC-LEVEL MODEL
# ================================
print("\n" + "="*80)
print("SETUP A: SOC-LEVEL MODEL")
print("="*80)
print("\nAggregating to SOC level...")

# Aggregate to SOC level
soc_agg = df_clean.groupby('soc_6digit').agg({
    'api_usage_count': 'sum',  # U_s = total Claude usage mass
    'TOT_EMP': 'first',  # E_s = employment
    'wage_annual': 'first',  # W_s = annual mean wage
    'wage_hourly': 'first',  # hourly wage
    'OCC_TITLE': 'first',  # occupation title
    'is_core_task': 'mean',  # share of core tasks
    'match_score': 'mean',  # average match quality
    'is_ambiguous': 'mean',  # share ambiguous
    'n_candidate_socs': 'mean'  # average ambiguity
}).reset_index()

# Rename for clarity
soc_agg.columns = ['soc_6digit', 'usage_total', 'employment', 'wage_annual', 'wage_hourly',
                   'occ_title', 'share_core', 'avg_match_score', 'share_ambiguous', 'avg_n_candidates']

# Create usage intensity (usage per worker)
soc_agg['usage_per_worker'] = soc_agg['usage_total'] / soc_agg['employment']

# Log transformations
soc_agg['log_wage'] = np.log(soc_agg['wage_annual'])
soc_agg['log_employment'] = np.log(soc_agg['employment'])
soc_agg['log_usage_intensity'] = np.log(soc_agg['usage_per_worker'] + 1e-6)  # small constant for zeros

print(f"\nSOC-level dataset:")
print(f"  Number of unique SOCs: {len(soc_agg):,}")
print(f"  SOCs with zero Claude usage: {(soc_agg['usage_total'] == 0).sum():,}")
print(f"  Mean usage per SOC: {soc_agg['usage_total'].mean():.1f}")
print(f"  Mean employment per SOC: {soc_agg['employment'].mean():.0f}")
print(f"  Mean annual wage: ${soc_agg['wage_annual'].mean():,.0f}")

print(f"\nDescriptive statistics (SOC level):")
print(soc_agg[['usage_total', 'usage_per_worker', 'employment', 'wage_annual', 'share_core']].describe())

# MODEL A1: Poisson with employment offset
print("\n" + "-"*80)
print("MODEL A1: Poisson regression (usage ~ wage, with employment offset)")
print("-"*80)

# Prepare data for Poisson
poisson_data = soc_agg[['usage_total', 'log_wage', 'log_employment', 'share_core', 'avg_match_score']].dropna()
poisson_data = poisson_data[poisson_data['usage_total'] >= 0]  # Poisson requires non-negative integers

# Round usage to integers for Poisson
poisson_data['usage_int'] = poisson_data['usage_total'].round().astype(int)

print(f"\nPoisson dataset: {len(poisson_data):,} SOCs")

# Fit Poisson model with offset
# log(E[usage]) = α + β*log(wage) + γ*share_core + δ*match_score + log(employment)
poisson_model = Poisson(
    endog=poisson_data['usage_int'],
    exog=sm.add_constant(poisson_data[['log_wage', 'share_core', 'avg_match_score']]),
    offset=poisson_data['log_employment']
).fit(cov_type='HC3')  # Robust standard errors

print("\n" + poisson_model.summary().as_text())

# MODEL A2: Negative Binomial (for overdispersion)
print("\n" + "-"*80)
print("MODEL A2: Negative Binomial regression (allows overdispersion)")
print("-"*80)

try:
    nb_model = NegativeBinomial(
        endog=poisson_data['usage_int'],
        exog=sm.add_constant(poisson_data[['log_wage', 'share_core', 'avg_match_score']]),
        offset=poisson_data['log_employment']
    ).fit(cov_type='HC3', maxiter=100)

    print("\n" + nb_model.summary().as_text())

    # Check for overdispersion
    print(f"\nOverdispersion test:")
    print(f"  Poisson mean prediction: {poisson_model.predict().mean():.2f}")
    print(f"  NB alpha (dispersion): {nb_model.params.get('alpha', 'N/A')}")
    print(f"  NB log-likelihood: {nb_model.llf:.2f}")
    print(f"  Poisson log-likelihood: {poisson_model.llf:.2f}")
    print(f"  LR test statistic (2*(LLnb - LLpoisson)): {2*(nb_model.llf - poisson_model.llf):.2f}")

    nb_converged = True
    nb_beta = nb_model.params['log_wage']
    nb_se = nb_model.bse['log_wage']
    nb_pval = nb_model.pvalues['log_wage']

except Exception as e:
    print(f"\n⚠️  NegativeBinomial failed to converge: {str(e)}")
    print("This is common with extreme count data. Using Poisson as primary specification.")
    nb_converged = False
    nb_beta = np.nan
    nb_se = np.nan
    nb_pval = np.nan
    nb_model = None

# MODEL A3: Log-linear OLS (alternative specification)
print("\n" + "-"*80)
print("MODEL A3: Log-linear OLS (log(usage_per_worker + c) ~ log(wage))")
print("-"*80)

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
print("\nUnit of analysis: (SOC, task) pairs")

# Prepare task-level data
task_data = df_clean.copy()
task_data['log_usage_plus1'] = np.log(1 + task_data['api_usage_count'])
task_data['log_wage'] = np.log(task_data['wage_annual'])
task_data['is_ambiguous_num'] = task_data['is_ambiguous'].astype(int)  # Convert boolean to int

print(f"\nTask-level dataset:")
print(f"  Number of (SOC, task) observations: {len(task_data):,}")
print(f"  Number of unique SOCs: {task_data['soc_6digit'].nunique():,}")
print(f"  Mean tasks per SOC: {len(task_data) / task_data['soc_6digit'].nunique():.1f}")

# MODEL B1: Task-level regression with clustering
print("\n" + "-"*80)
print("MODEL B1: Task-level OLS with SOC clustering")
print("Formula: log(1 + usage) ~ log(wage) + is_core + match_score + is_ambiguous")
print("-"*80)

task_reg_data = task_data[['log_usage_plus1', 'log_wage', 'is_core_task', 'match_score', 'is_ambiguous_num', 'soc_6digit']].dropna()

task_model = OLS(
    endog=task_reg_data['log_usage_plus1'],
    exog=sm.add_constant(task_reg_data[['log_wage', 'is_core_task', 'match_score', 'is_ambiguous_num']])
).fit(cov_type='cluster', cov_kwds={'groups': task_reg_data['soc_6digit']})  # Cluster SE at SOC level

print("\n" + task_model.summary().as_text())

# ================================
# SENSITIVITY ANALYSES
# ================================
print("\n" + "="*80)
print("SENSITIVITY ANALYSES")
print("="*80)

# SENSITIVITY 1: Exclude ambiguous mappings
print("\nSENSITIVITY 1: Excluding ambiguous mappings")
print("-"*80)

# SOC-level (re-aggregate without ambiguous)
soc_agg_no_amb = df_clean[~df_clean['is_ambiguous']].groupby('soc_6digit').agg({
    'api_usage_count': 'sum',
    'TOT_EMP': 'first',
    'wage_annual': 'first',
    'is_core_task': 'mean',
    'match_score': 'mean'
}).reset_index()

soc_agg_no_amb['log_wage'] = np.log(soc_agg_no_amb['wage_annual'])
soc_agg_no_amb['log_employment'] = np.log(soc_agg_no_amb['TOT_EMP'])
soc_agg_no_amb['usage_int'] = soc_agg_no_amb['api_usage_count'].round().astype(int)

print(f"SOCs in non-ambiguous sample: {len(soc_agg_no_amb):,}")

poisson_no_amb = Poisson(
    endog=soc_agg_no_amb['usage_int'],
    exog=sm.add_constant(soc_agg_no_amb[['log_wage', 'is_core_task', 'match_score']].fillna(0)),
    offset=soc_agg_no_amb['log_employment']
).fit(cov_type='HC3')

print("\nPoisson (excluding ambiguous):")
print(poisson_no_amb.summary().as_text())

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
# RESULTS SUMMARY TABLE
# ================================
print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80)

summary_results = pd.DataFrame({
    'Model': [
        'A1: Poisson (full sample)',
        'A1: Poisson (no ambiguous)',
        'A2: Negative Binomial',
        'A3: Log-linear OLS',
        'B1: Task-level OLS (full)',
        'B1: Task-level OLS (no amb)'
    ],
    'Beta_log_wage': [
        poisson_model.params['log_wage'],
        poisson_no_amb.params['log_wage'],
        nb_beta,
        ols_model.params['log_wage'],
        task_model.params['log_wage'],
        task_model_no_amb.params['log_wage']
    ],
    'SE': [
        poisson_model.bse['log_wage'],
        poisson_no_amb.bse['log_wage'],
        nb_se,
        ols_model.bse['log_wage'],
        task_model.bse['log_wage'],
        task_model_no_amb.bse['log_wage']
    ],
    'P_value': [
        poisson_model.pvalues['log_wage'],
        poisson_no_amb.pvalues['log_wage'],
        nb_pval,
        ols_model.pvalues['log_wage'],
        task_model.pvalues['log_wage'],
        task_model_no_amb.pvalues['log_wage']
    ],
    'N': [
        len(poisson_data),
        len(soc_agg_no_amb),
        len(poisson_data) if nb_converged else 0,
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

# Save results
summary_results.to_csv(OUTPUT_DIR / 'model_summary.csv', index=False)
print(f"\n✓ Results saved to: {OUTPUT_DIR / 'model_summary.csv'}")

# Save SOC-level aggregated data
soc_agg.to_csv(OUTPUT_DIR / 'soc_level_data.csv', index=False)
print(f"✓ SOC-level data saved to: {OUTPUT_DIR / 'soc_level_data.csv'}")

print("\n" + "="*80)
print("ESTIMATION COMPLETE")
print("="*80)
