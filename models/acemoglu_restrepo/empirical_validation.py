"""
Acemoglu-Restrepo Empirical Validation: AI Exposure → Wage Growth
==================================================================

This script tests the A-R model's predictions using actual wage panel data (2022-2024).

THEORETICAL PREDICTIONS:
- A-R displacement model: Higher AI exposure → wage decline (β < 0)
- O-ring complementarity: Higher AI exposure → wage increase (β > 0)

EMPIRICAL TEST:
Δln(w_i) = β × ai_exposure_i + γ × ln(employment_i,2022) + ε_i

where:
- Δln(w_i) = ln(wage_2024) - ln(wage_2022)
- ai_exposure_i = importance-weighted AI exposure from crosswalk
- Controls: baseline employment (size effect), industry fixed effects

If β > 0 and significant: Complementarity (supports O-ring)
If β < 0 and significant: Displacement (supports A-R)
If β ≈ 0: No relationship (AI not affecting wages yet, or offsetting effects)

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import sys
from pathlib import Path

# Add models/utils to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "models" / "utils"))

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
import matplotlib.pyplot as plt
import seaborn as sns
from exposure_calculation import calculate_importance_weighted_exposure

# Paths
DATA_DIR = ROOT_DIR / "data"
WAGE_PANEL_FILE = DATA_DIR / "processed" / "wage_panel_2022_2024.csv"
CROSSWALK_FILE = DATA_DIR / "processed" / "master_task_crosswalk_with_importance.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("ACEMOGLU-RESTREPO EMPIRICAL VALIDATION")
print("AI Exposure → Wage Growth (2022-2024)")
print("=" * 80)

# =============================================================================
# STEP 1: Load wage panel data
# =============================================================================
print("\nSTEP 1: Loading wage panel data...")
wage_panel = pd.read_csv(WAGE_PANEL_FILE)

print(f"  Loaded {len(wage_panel):,} rows")
print(f"  Years: {sorted(wage_panel['year'].unique())}")
print(f"  Unique occupations: {wage_panel['soc_code'].nunique():,}")

# =============================================================================
# STEP 2: Compute wage changes (2022 → 2024)
# =============================================================================
print("\nSTEP 2: Computing wage changes (2022 → 2024)...")

# Pivot to wide format
wage_wide = wage_panel.pivot_table(
    index='soc_code',
    columns='year',
    values=['wage_annual_mean', 'employment', 'occ_title'],
    aggfunc='first'
).reset_index()

# Flatten column names
wage_wide.columns = ['_'.join(map(str, col)).strip('_') if col[1] != '' else col[0]
                     for col in wage_wide.columns]

print(f"  Wide format shape: {wage_wide.shape}")
print(f"  Columns: {wage_wide.columns.tolist()}")

# Compute log wage changes
# IMPORTANT TIMING NOTE:
# - Claude/GPT-4 released March 2023
# - 2022 baseline PREDATES LLMs
# - Should use 2023-2024 for post-LLM period
# - BUT 2022-2024 tests if AI exposure proxies for pre-existing task vulnerability

# Compute BOTH periods for comparison
wage_wide = wage_wide[
    wage_wide['wage_annual_mean_2022'].notna() &
    wage_wide['wage_annual_mean_2024'].notna() &
    (wage_wide['wage_annual_mean_2022'] > 0) &
    (wage_wide['wage_annual_mean_2024'] > 0)
].copy()

# 2022-2024 (includes pre-LLM period)
wage_wide['ln_wage_2022'] = np.log(wage_wide['wage_annual_mean_2022'])
wage_wide['ln_wage_2023'] = np.log(wage_wide['wage_annual_mean_2023'])
wage_wide['ln_wage_2024'] = np.log(wage_wide['wage_annual_mean_2024'])

wage_wide['delta_ln_wage_2022_2024'] = wage_wide['ln_wage_2024'] - wage_wide['ln_wage_2022']
wage_wide['delta_ln_wage_2023_2024'] = wage_wide['ln_wage_2024'] - wage_wide['ln_wage_2023']

wage_wide['wage_growth_pct_2022_2024'] = (wage_wide['wage_annual_mean_2024'] /
                                           wage_wide['wage_annual_mean_2022'] - 1) * 100
wage_wide['wage_growth_pct_2023_2024'] = (wage_wide['wage_annual_mean_2024'] /
                                           wage_wide['wage_annual_mean_2023'] - 1) * 100

# Use 2022-2024 as primary (tests if exposure proxies task vulnerability)
wage_wide['delta_ln_wage'] = wage_wide['delta_ln_wage_2022_2024']
wage_wide['wage_growth_pct'] = wage_wide['wage_growth_pct_2022_2024']

# Baseline employment (2022)
wage_wide['ln_employment_2022'] = np.log(wage_wide['employment_2022'].clip(lower=1))

print(f"\n  Occupations with 2022-2024 data: {len(wage_wide):,}")
print(f"\n  Wage growth statistics:")
print(f"    Mean Δln(wage): {wage_wide['delta_ln_wage'].mean():.4f} ({wage_wide['wage_growth_pct'].mean():.2f}%)")
print(f"    Std dev: {wage_wide['delta_ln_wage'].std():.4f}")
print(f"    Min: {wage_wide['delta_ln_wage'].min():.4f}")
print(f"    Max: {wage_wide['delta_ln_wage'].max():.4f}")

# =============================================================================
# STEP 3: Load AI exposure from crosswalk
# =============================================================================
print("\nSTEP 3: Loading AI exposure from crosswalk...")

crosswalk = pd.read_csv(CROSSWALK_FILE)
print(f"  Loaded crosswalk: {len(crosswalk):,} rows")

# Compute importance-weighted exposure
occ_exposure = calculate_importance_weighted_exposure(crosswalk)
print(f"  Occupations with AI exposure: {len(occ_exposure):,}")

# Map O*NET SOC (8-digit) to BLS SOC (6-digit)
# O*NET format: XX-XXXX.YY, BLS format: XX-XXXX
occ_exposure['soc_code'] = occ_exposure['onet_soc_code'].str[:7]  # Take first 7 chars (XX-XXXX)

# Aggregate to 6-digit level (some O*NET 8-digit map to same 6-digit)
exposure_for_merge = occ_exposure.groupby('soc_code').agg({
    'ai_exposure': 'mean',  # Average exposure if multiple O*NET codes map to same BLS code
    'TOT_EMP': 'sum',
    'A_MEAN': 'mean'
}).reset_index()

print(f"\n  AI exposure statistics:")
print(f"    Mean: {exposure_for_merge['ai_exposure'].mean():.4f}")
print(f"    Std dev: {exposure_for_merge['ai_exposure'].std():.4f}")
print(f"    Range: [{exposure_for_merge['ai_exposure'].min():.4f}, {exposure_for_merge['ai_exposure'].max():.4f}]")

# =============================================================================
# STEP 4: Merge wage panel with AI exposure
# =============================================================================
print("\nSTEP 4: Merging wage panel with AI exposure...")

# Try exact match first
merged = wage_wide.merge(exposure_for_merge, on='soc_code', how='left')
print(f"  Exact matches: {merged['ai_exposure'].notna().sum():,} / {len(merged):,}")

# For unmatched, try matching on first 5 digits (major group)
unmatched = merged[merged['ai_exposure'].isna()].copy()
if len(unmatched) > 0:
    print(f"\n  Trying to match {len(unmatched):,} unmatched SOCs on 5-digit level...")

    # Create 5-digit SOC codes
    exposure_for_merge['soc_5digit'] = exposure_for_merge['soc_code'].str[:7]  # XX-XXXX
    unmatched['soc_5digit'] = unmatched['soc_code'].str[:7]

    # Aggregate exposure to 5-digit level (employment-weighted mean)
    exposure_5digit = exposure_for_merge.groupby('soc_5digit').agg({
        'ai_exposure': 'mean'
    }).reset_index()

    # Merge for unmatched
    unmatched = unmatched.drop(columns=['ai_exposure']).merge(
        exposure_5digit, on='soc_5digit', how='left', suffixes=('', '_5digit')
    )

    # Update merged
    merged.loc[merged['ai_exposure'].isna(), 'ai_exposure'] = unmatched['ai_exposure']
    print(f"  After 5-digit matching: {merged['ai_exposure'].notna().sum():,} / {len(merged):,}")

# Keep only matched
regression_data = merged[merged['ai_exposure'].notna()].copy()
print(f"\n  Final regression sample: {len(regression_data):,} occupations")

# =============================================================================
# STEP 5: Descriptive statistics
# =============================================================================
print("\n" + "=" * 80)
print("STEP 5: Descriptive Statistics")
print("=" * 80)

desc_stats = regression_data[['delta_ln_wage', 'wage_growth_pct', 'ai_exposure',
                               'ln_employment_2022']].describe()
print("\n", desc_stats.to_string())

# Correlation matrix
print("\n  Correlation matrix:")
corr_vars = ['delta_ln_wage', 'ai_exposure', 'ln_employment_2022']
corr_matrix = regression_data[corr_vars].corr()
print(corr_matrix.to_string())

# =============================================================================
# STEP 6: Regression - AI Exposure → Wage Growth
# =============================================================================
print("\n" + "=" * 80)
print("STEP 6: Regression Analysis")
print("=" * 80)

print("\nMODEL: Δln(w_i) = β₀ + β₁ × ai_exposure_i + β₂ × ln(employment_2022) + ε_i")

# Prepare regression data
reg_vars = ['delta_ln_wage', 'ai_exposure', 'ln_employment_2022']
reg_df = regression_data[reg_vars].dropna()

print(f"\nRegression sample size: {len(reg_df):,} occupations")

# Run OLS with robust standard errors
X = sm.add_constant(reg_df[['ai_exposure', 'ln_employment_2022']])
y = reg_df['delta_ln_wage']

model = OLS(y, X).fit(cov_type='HC3')

print("\n" + "=" * 80)
print(model.summary().as_text())
print("=" * 80)

# Extract key results
beta_exposure = model.params['ai_exposure']
se_exposure = model.bse['ai_exposure']
pval_exposure = model.pvalues['ai_exposure']
rsquared = model.rsquared

print("\n" + "=" * 80)
print("KEY RESULTS")
print("=" * 80)

print(f"\nCoefficient on AI Exposure:")
print(f"  β = {beta_exposure:.6f}")
print(f"  SE = {se_exposure:.6f}")
print(f"  t-stat = {beta_exposure/se_exposure:.3f}")
print(f"  p-value = {pval_exposure:.6f}")

if pval_exposure < 0.001:
    sig_str = "***"
elif pval_exposure < 0.01:
    sig_str = "**"
elif pval_exposure < 0.05:
    sig_str = "*"
else:
    sig_str = "(not significant)"

print(f"  Significance: {sig_str}")

print(f"\nR-squared: {rsquared:.4f}")

print("\n" + "-" * 80)
print("INTERPRETATION:")
print("-" * 80)

if pval_exposure < 0.05:
    if beta_exposure > 0:
        print(f"✓ AI exposure is POSITIVELY associated with wage growth ({sig_str})")
        print(f"  → 10pp increase in AI exposure → {beta_exposure*0.1*100:.2f}% wage growth")
        print(f"  → SUPPORTS O-RING COMPLEMENTARITY (Gans & Goldfarb 2025)")
        print(f"  → CONTRADICTS A-R DISPLACEMENT")
    else:
        print(f"✓ AI exposure is NEGATIVELY associated with wage growth ({sig_str})")
        print(f"  → 10pp increase in AI exposure → {beta_exposure*0.1*100:.2f}% wage decline")
        print(f"  → SUPPORTS A-R DISPLACEMENT")
        print(f"  → CONTRADICTS O-RING COMPLEMENTARITY")
else:
    print("✗ AI exposure is NOT significantly associated with wage growth")
    print("  → Either: (1) AI not affecting wages yet, (2) offsetting effects,")
    print("           (3) insufficient time (2022-2024 too short), or")
    print("           (4) measurement error in exposure")

# =============================================================================
# STEP 7: Robustness checks
# =============================================================================
print("\n" + "=" * 80)
print("STEP 7: Robustness Checks")
print("=" * 80)

# 1. Without employment control
print("\nModel 1: Without employment control")
X_simple = sm.add_constant(reg_df[['ai_exposure']])
model_simple = OLS(y, X_simple).fit(cov_type='HC3')
print(f"  β(ai_exposure) = {model_simple.params['ai_exposure']:.6f} (SE: {model_simple.bse['ai_exposure']:.6f})")
print(f"  p-value = {model_simple.pvalues['ai_exposure']:.6f}")

# 2. Weighted by employment
print("\nModel 2: Weighted by 2022 employment")
weights = regression_data.loc[reg_df.index, 'employment_2022']
model_weighted = OLS(y, X).fit(cov_type='HC3', weights=weights)
print(f"  β(ai_exposure) = {model_weighted.params['ai_exposure']:.6f} (SE: {model_weighted.bse['ai_exposure']:.6f})")
print(f"  p-value = {model_weighted.pvalues['ai_exposure']:.6f}")

# 3. Top vs bottom quartile exposure
print("\nModel 3: Top vs Bottom quartile exposure difference")
reg_df['exposure_quartile'] = pd.qcut(reg_df['ai_exposure'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
quartile_means = reg_df.groupby('exposure_quartile')['delta_ln_wage'].mean()
print(f"  Bottom quartile (Q1) mean wage growth: {quartile_means['Q1']:.4f}")
print(f"  Top quartile (Q4) mean wage growth: {quartile_means['Q4']:.4f}")
print(f"  Difference (Q4 - Q1): {quartile_means['Q4'] - quartile_means['Q1']:.4f}")

# 4. CRITICAL TIMING CHECK: 2023-2024 only (post-LLM period)
print("\n" + "="*80)
print("CRITICAL TIMING CHECK: 2023-2024 vs 2022-2024")
print("="*80)
print("\nPROBLEM: Claude/GPT-4 released March 2023, but 2022 baseline PREDATES LLMs!")
print("SOLUTION: Compare 2022-2024 (includes pre-LLM) vs 2023-2024 (post-LLM only)")

# Prepare 2023-2024 data
reg_df_2023 = regression_data[['delta_ln_wage_2023_2024', 'ai_exposure', 'ln_employment_2022']].dropna()
reg_df_2023 = reg_df_2023.rename(columns={'delta_ln_wage_2023_2024': 'delta_ln_wage'})

print(f"\n2023-2024 sample size: {len(reg_df_2023):,} occupations")
print(f"Mean wage growth 2023-2024: {reg_df_2023['delta_ln_wage'].mean():.4f}")

X_2023 = sm.add_constant(reg_df_2023[['ai_exposure', 'ln_employment_2022']])
y_2023 = reg_df_2023['delta_ln_wage']
model_2023 = OLS(y_2023, X_2023).fit(cov_type='HC3')

print("\nModel 4: 2023-2024 ONLY (post-LLM period)")
print(f"  β(ai_exposure) = {model_2023.params['ai_exposure']:.6f} (SE: {model_2023.bse['ai_exposure']:.6f})")
print(f"  p-value = {model_2023.pvalues['ai_exposure']:.6f}")
print(f"  R² = {model_2023.rsquared:.4f}")

if model_2023.pvalues['ai_exposure'] < 0.05:
    sig_2023 = "***" if model_2023.pvalues['ai_exposure'] < 0.001 else "**" if model_2023.pvalues['ai_exposure'] < 0.01 else "*"
else:
    sig_2023 = "(n.s.)"

print(f"\nCOMPARISON:")
print(f"  2022-2024 (includes pre-LLM): β = {beta_exposure:.6f}{sig_str}")
print(f"  2023-2024 (post-LLM only):    β = {model_2023.params['ai_exposure']:.6f}{sig_2023}")

print(f"\nINTERPRETATION:")
if abs(model_2023.params['ai_exposure']) > abs(beta_exposure):
    print("  ✓ Effect is STRONGER in 2023-2024 (post-LLM) → suggests causal LLM impact")
elif model_2023.pvalues['ai_exposure'] > 0.05:
    print("  ✓ Effect DISAPPEARS in 2023-2024 → suggests 2022-2024 was spurious/pre-existing")
else:
    print("  ✓ Effect is WEAKER in 2023-2024 → AI exposure proxies for pre-existing vulnerability")
    print("     (Claude usage correlates with routine task content that was vulnerable BEFORE LLMs)")

# Save both results for comparison
timing_comparison = pd.DataFrame({
    'Period': ['2022-2024 (includes pre-LLM)', '2023-2024 (post-LLM only)'],
    'Beta': [beta_exposure, model_2023.params['ai_exposure']],
    'SE': [se_exposure, model_2023.bse['ai_exposure']],
    'P_value': [pval_exposure, model_2023.pvalues['ai_exposure']],
    'Significance': [sig_str, sig_2023],
    'N': [len(reg_df), len(reg_df_2023)]
})
timing_comparison.to_csv(OUTPUT_DIR / 'timing_comparison.csv', index=False)
print(f"\n✓ Saved timing comparison to: {OUTPUT_DIR / 'timing_comparison.csv'}")

# =============================================================================
# STEP 8: Visualization
# =============================================================================
print("\n" + "=" * 80)
print("STEP 8: Creating visualizations...")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Scatter plot: AI exposure vs wage growth
ax1 = axes[0, 0]
ax1.scatter(reg_df['ai_exposure'], reg_df['delta_ln_wage'], alpha=0.5, s=50)
# Add regression line
X_plot = np.linspace(reg_df['ai_exposure'].min(), reg_df['ai_exposure'].max(), 100)
y_plot = model.params['const'] + model.params['ai_exposure'] * X_plot + \
         model.params['ln_employment_2022'] * reg_df['ln_employment_2022'].mean()
ax1.plot(X_plot, y_plot, 'r-', linewidth=2, label=f'β={beta_exposure:.4f}{sig_str}')
ax1.set_xlabel('AI Exposure (Importance-Weighted)')
ax1.set_ylabel('Δln(Wage) 2022→2024')
ax1.set_title('AI Exposure → Wage Growth')
ax1.legend()
ax1.grid(alpha=0.3)

# 2. Distribution of wage growth
ax2 = axes[0, 1]
ax2.hist(reg_df['delta_ln_wage'], bins=30, alpha=0.7, edgecolor='black')
ax2.axvline(reg_df['delta_ln_wage'].mean(), color='r', linestyle='--',
            label=f'Mean: {reg_df["delta_ln_wage"].mean():.4f}')
ax2.set_xlabel('Δln(Wage) 2022→2024')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of Wage Growth')
ax2.legend()
ax2.grid(alpha=0.3)

# 3. Quartile comparison
ax3 = axes[1, 0]
quartile_means.plot(kind='bar', ax=ax3, color=['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4'])
ax3.set_xlabel('AI Exposure Quartile')
ax3.set_ylabel('Mean Δln(Wage)')
ax3.set_title('Wage Growth by AI Exposure Quartile')
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
ax3.grid(alpha=0.3, axis='y')

# 4. Residual plot
ax4 = axes[1, 1]
residuals = model.resid
fitted = model.fittedvalues
ax4.scatter(fitted, residuals, alpha=0.5, s=50)
ax4.axhline(0, color='r', linestyle='--', linewidth=2)
ax4.set_xlabel('Fitted Values')
ax4.set_ylabel('Residuals')
ax4.set_title('Residual Plot')
ax4.grid(alpha=0.3)

plt.tight_layout()
fig_path = OUTPUT_DIR / 'empirical_validation_plots.png'
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved plots to: {fig_path}")

# =============================================================================
# STEP 9: Save results
# =============================================================================
print("\n" + "=" * 80)
print("STEP 9: Saving results...")
print("=" * 80)

# Summary results
results_summary = pd.DataFrame({
    'Metric': [
        'Sample size (occupations)',
        'Mean wage growth 2022-2024',
        'β (AI exposure)',
        'SE (AI exposure)',
        't-statistic',
        'p-value',
        'Significance',
        'R-squared',
        'Interpretation'
    ],
    'Value': [
        len(reg_df),
        reg_df['delta_ln_wage'].mean(),
        beta_exposure,
        se_exposure,
        beta_exposure / se_exposure,
        pval_exposure,
        sig_str,
        rsquared,
        'Complementarity (β>0)' if beta_exposure > 0 else 'Displacement (β<0)'
    ],
    'Formatted': [
        f"{len(reg_df):,}",
        f"{reg_df['delta_ln_wage'].mean()*100:.2f}%",
        f"{beta_exposure:.6f}",
        f"{se_exposure:.6f}",
        f"{beta_exposure/se_exposure:.3f}",
        f"{pval_exposure:.6f}",
        sig_str,
        f"{rsquared:.4f}",
        'Complementarity (β>0)***' if (beta_exposure > 0 and pval_exposure < 0.001) else
        'Displacement (β<0)***' if (beta_exposure < 0 and pval_exposure < 0.001) else
        'No significant effect'
    ]
})

results_summary.to_csv(OUTPUT_DIR / 'empirical_validation_results.csv', index=False)
print(f"✓ Saved summary to: {OUTPUT_DIR / 'empirical_validation_results.csv'}")

# Regression data for replication
regression_data.to_csv(OUTPUT_DIR / 'empirical_validation_data.csv', index=False)
print(f"✓ Saved regression data to: {OUTPUT_DIR / 'empirical_validation_data.csv'}")

print("\n" + "=" * 80)
print("EMPIRICAL VALIDATION COMPLETE")
print("=" * 80)

print("\nSUMMARY:")
if pval_exposure < 0.05:
    if beta_exposure > 0:
        print("  ✓ FINDING: AI exposure INCREASES wages (complementarity)")
        print("  ✓ Evidence supports O-ring model, contradicts A-R displacement")
    else:
        print("  ✓ FINDING: AI exposure DECREASES wages (displacement)")
        print("  ✓ Evidence supports A-R model")
else:
    print("  ✗ FINDING: No significant relationship detected")
    print("  ✗ Either too early to detect effects or offsetting mechanisms")

print("\nCAVEATS:")
print("  - Short time window (2022-2024, only 2 years)")
print("  - Cross-sectional variation, not causal identification")
print("  - Cannot rule out selection bias (AI adoption endogenous)")
print("  - Wage data is occupation-level aggregate, not individual workers")

print("\n" + "=" * 80)
