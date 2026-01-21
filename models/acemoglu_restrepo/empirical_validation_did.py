"""
Acemoglu-Restrepo Empirical Validation: DIFFERENCE-IN-DIFFERENCES Design
=========================================================================

PROPER RESEARCH DESIGN:

Research Question: Do LLMs cause wage displacement in high-AI-exposure occupations?

Treatment: High AI exposure (measured from 2025 Claude API usage)
Control: Low AI exposure

Timeline:
- Pre-period: 2022-2023 (mostly before LLM release in March 2023)
- Post-period: 2023-2024 (full year post-LLM)

Diff-in-Diff Specification:
----------------------------
Δln(wage_it) = β₀ + β₁·HighExposure_i + β₂·Post_t + β₃·(HighExposure_i × Post_t) + ε_it

Where:
- β₁: Pre-existing wage growth difference between high/low exposure groups
- β₂: Common time trend affecting all occupations
- β₃: DIFF-IN-DIFF ESTIMATOR - causal effect of LLMs on high-exposure occupations

If β₃ < 0 and significant: LLMs cause displacement
If β₃ ≈ 0: No additional LLM effect beyond pre-existing trends

Alternative Specifications:
---------------------------
1. Continuous exposure (interaction with continuous AI exposure variable)
2. Quartile comparisons (Q4 vs Q1)
3. Panel regression with occupation fixed effects

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
print("DIFF-IN-DIFF: AI EXPOSURE → WAGE DISPLACEMENT")
print("Rigorous Causal Design with Pre/Post Comparison")
print("=" * 80)

# =============================================================================
# STEP 1: Load and prepare data
# =============================================================================
print("\nSTEP 1: Loading data...")

# Load wage panel
wage_panel = pd.read_csv(WAGE_PANEL_FILE)
print(f"  Wage panel: {len(wage_panel):,} rows")

# Load AI exposure
crosswalk = pd.read_csv(CROSSWALK_FILE)
occ_exposure = calculate_importance_weighted_exposure(crosswalk)

# Map O*NET to BLS SOC codes
occ_exposure['soc_code'] = occ_exposure['onet_soc_code'].str[:7]
exposure_for_merge = occ_exposure.groupby('soc_code').agg({
    'ai_exposure': 'mean',
    'TOT_EMP': 'sum'
}).reset_index()

print(f"  AI exposure: {len(exposure_for_merge):,} occupations")
print(f"  Mean exposure: {exposure_for_merge['ai_exposure'].mean():.3f}")

# =============================================================================
# STEP 2: Construct panel with wage changes
# =============================================================================
print("\nSTEP 2: Constructing panel dataset...")

# Reshape to wide format
wage_wide = wage_panel.pivot_table(
    index='soc_code',
    columns='year',
    values=['wage_annual_mean', 'employment', 'occ_title'],
    aggfunc='first'
).reset_index()

wage_wide.columns = ['_'.join(map(str, col)).strip('_') if col[1] != '' else col[0]
                     for col in wage_wide.columns]

# Filter to complete cases
wage_wide = wage_wide[
    wage_wide['wage_annual_mean_2022'].notna() &
    wage_wide['wage_annual_mean_2023'].notna() &
    wage_wide['wage_annual_mean_2024'].notna() &
    (wage_wide['wage_annual_mean_2022'] > 0) &
    (wage_wide['wage_annual_mean_2023'] > 0) &
    (wage_wide['wage_annual_mean_2024'] > 0)
].copy()

print(f"  Occupations with complete 2022-2024 data: {len(wage_wide):,}")

# Compute wage changes for both periods
wage_wide['ln_wage_2022'] = np.log(wage_wide['wage_annual_mean_2022'])
wage_wide['ln_wage_2023'] = np.log(wage_wide['wage_annual_mean_2023'])
wage_wide['ln_wage_2024'] = np.log(wage_wide['wage_annual_mean_2024'])

wage_wide['delta_ln_wage_pre'] = wage_wide['ln_wage_2023'] - wage_wide['ln_wage_2022']  # 2022-2023
wage_wide['delta_ln_wage_post'] = wage_wide['ln_wage_2024'] - wage_wide['ln_wage_2023']  # 2023-2024

print(f"\n  Pre-period (2022-2023) mean wage growth: {wage_wide['delta_ln_wage_pre'].mean():.4f}")
print(f"  Post-period (2023-2024) mean wage growth: {wage_wide['delta_ln_wage_post'].mean():.4f}")

# Merge with AI exposure
panel_data = wage_wide.merge(exposure_for_merge, on='soc_code', how='left')
panel_data = panel_data[panel_data['ai_exposure'].notna()].copy()

print(f"\n  Panel data with AI exposure: {len(panel_data):,} occupations")

# =============================================================================
# STEP 3: Define treatment groups
# =============================================================================
print("\n" + "=" * 80)
print("STEP 3: Defining Treatment Groups")
print("=" * 80)

# Binary treatment: above/below median exposure
median_exposure = panel_data['ai_exposure'].median()
panel_data['high_exposure'] = (panel_data['ai_exposure'] > median_exposure).astype(int)

print(f"\nMedian exposure: {median_exposure:.3f}")
print(f"High-exposure group (above median): {panel_data['high_exposure'].sum():,} occupations")
print(f"Low-exposure group (below median): {(1-panel_data['high_exposure']).sum():,} occupations")

# Also create quartiles for robustness
panel_data['exposure_quartile'] = pd.qcut(panel_data['ai_exposure'], q=4,
                                           labels=['Q1', 'Q2', 'Q3', 'Q4'])

# =============================================================================
# STEP 4: Descriptive statistics by treatment group
# =============================================================================
print("\n" + "=" * 80)
print("STEP 4: Descriptive Statistics by Treatment Group")
print("=" * 80)

print("\nPRE-PERIOD (2022-2023):")
pre_high = panel_data[panel_data['high_exposure'] == 1]['delta_ln_wage_pre'].mean()
pre_low = panel_data[panel_data['high_exposure'] == 0]['delta_ln_wage_pre'].mean()
print(f"  High-exposure group: {pre_high:.4f} ({pre_high*100:.2f}%)")
print(f"  Low-exposure group: {pre_low:.4f} ({pre_low*100:.2f}%)")
print(f"  Difference (High - Low): {pre_high - pre_low:.4f}")

print("\nPOST-PERIOD (2023-2024):")
post_high = panel_data[panel_data['high_exposure'] == 1]['delta_ln_wage_post'].mean()
post_low = panel_data[panel_data['high_exposure'] == 0]['delta_ln_wage_post'].mean()
print(f"  High-exposure group: {post_high:.4f} ({post_high*100:.2f}%)")
print(f"  Low-exposure group: {post_low:.4f} ({post_low*100:.2f}%)")
print(f"  Difference (High - Low): {post_high - post_low:.4f}")

print("\n" + "-" * 80)
print("DIFF-IN-DIFF ESTIMATE (Simple):")
print("-" * 80)
did_simple = (post_high - post_low) - (pre_high - pre_low)
print(f"  [(High_post - Low_post) - (High_pre - Low_pre)]")
print(f"  = [{post_high:.4f} - {post_low:.4f}] - [{pre_high:.4f} - {pre_low:.4f}]")
print(f"  = {post_high - post_low:.4f} - {pre_high - pre_low:.4f}")
print(f"  = {did_simple:.4f}")
print()
if did_simple < 0:
    print(f"  → High-exposure occupations experienced {abs(did_simple)*100:.2f}% ADDITIONAL wage decline")
    print(f"     relative to low-exposure occupations after LLM release")
else:
    print(f"  → High-exposure occupations experienced {did_simple*100:.2f}% RELATIVE wage gain")
    print(f"     (no displacement detected)")

# =============================================================================
# STEP 5: Regression-based Diff-in-Diff (Binary Treatment)
# =============================================================================
print("\n" + "=" * 80)
print("STEP 5: Regression Diff-in-Diff (Binary Treatment)")
print("=" * 80)

# Stack data into long format
panel_long = []
for _, row in panel_data.iterrows():
    # Pre-period observation
    panel_long.append({
        'soc_code': row['soc_code'],
        'occ_title': row['occ_title_2022'],
        'delta_ln_wage': row['delta_ln_wage_pre'],
        'post': 0,
        'high_exposure': row['high_exposure'],
        'ai_exposure': row['ai_exposure'],
        'ln_employment': np.log(row['employment_2022'])
    })
    # Post-period observation
    panel_long.append({
        'soc_code': row['soc_code'],
        'occ_title': row['occ_title_2023'],
        'delta_ln_wage': row['delta_ln_wage_post'],
        'post': 1,
        'high_exposure': row['high_exposure'],
        'ai_exposure': row['ai_exposure'],
        'ln_employment': np.log(row['employment_2023'])
    })

panel_long = pd.DataFrame(panel_long)
print(f"\nStacked panel: {len(panel_long):,} observations ({len(panel_data):,} occupations × 2 periods)")

# Diff-in-diff regression with interaction
panel_long['high_x_post'] = panel_long['high_exposure'] * panel_long['post']

X_did = sm.add_constant(panel_long[['high_exposure', 'post', 'high_x_post', 'ln_employment']])
y_did = panel_long['delta_ln_wage']

model_did = OLS(y_did, X_did).fit(cov_type='cluster', cov_kwds={'groups': panel_long['soc_code']})

print("\nDiff-in-Diff Regression:")
print("Δln(wage_it) = β₀ + β₁·HighExposure + β₂·Post + β₃·(HighExposure×Post) + β₄·ln(emp) + ε")
print("\n" + model_did.summary().as_text())

# Extract key coefficient
beta_did = model_did.params['high_x_post']
se_did = model_did.bse['high_x_post']
pval_did = model_did.pvalues['high_x_post']
tstat_did = beta_did / se_did

print("\n" + "=" * 80)
print("KEY RESULT: Diff-in-Diff Coefficient β₃")
print("=" * 80)
print(f"\nβ₃ (HighExposure × Post) = {beta_did:.6f}")
print(f"Standard Error = {se_did:.6f}")
print(f"t-statistic = {tstat_did:.3f}")
print(f"p-value = {pval_did:.6f}")

if pval_did < 0.001:
    sig_str = "***"
elif pval_did < 0.01:
    sig_str = "**"
elif pval_did < 0.05:
    sig_str = "*"
else:
    sig_str = "(n.s.)"

print(f"Significance: {sig_str}")

print("\n" + "-" * 80)
print("INTERPRETATION:")
print("-" * 80)

if pval_did < 0.05:
    if beta_did < 0:
        print(f"✓ SIGNIFICANT NEGATIVE EFFECT: High-exposure occupations experienced")
        print(f"  {abs(beta_did)*100:.2f}% ADDITIONAL wage decline after LLM release")
        print(f"  relative to low-exposure occupations.")
        print(f"\n  → CAUSAL EVIDENCE of LLM-induced displacement")
    else:
        print(f"✓ SIGNIFICANT POSITIVE EFFECT: High-exposure occupations experienced")
        print(f"  {beta_did*100:.2f}% ADDITIONAL wage growth after LLM release")
        print(f"  relative to low-exposure occupations.")
        print(f"\n  → CONTRADICTS displacement hypothesis")
else:
    print(f"✗ NO SIGNIFICANT DIFF-IN-DIFF EFFECT")
    print(f"  β₃ = {beta_did:.4f} (p = {pval_did:.3f})")
    print(f"\n  → No evidence that LLM release differentially affected high-exposure occupations")
    print(f"  → Pre-existing trends continue unchanged")

# =============================================================================
# STEP 6: Continuous Exposure Specification
# =============================================================================
print("\n" + "=" * 80)
print("STEP 6: Continuous Exposure Specification")
print("=" * 80)

# Interaction with continuous exposure variable
panel_long['exposure_x_post'] = panel_long['ai_exposure'] * panel_long['post']

X_did_cont = sm.add_constant(panel_long[['ai_exposure', 'post', 'exposure_x_post', 'ln_employment']])
model_did_cont = OLS(y_did, X_did_cont).fit(cov_type='cluster', cov_kwds={'groups': panel_long['soc_code']})

print("\nDiff-in-Diff Regression (Continuous Exposure):")
print("Δln(wage_it) = β₀ + β₁·Exposure + β₂·Post + β₃·(Exposure×Post) + β₄·ln(emp) + ε")
print("\n" + model_did_cont.summary().as_text())

beta_did_cont = model_did_cont.params['exposure_x_post']
se_did_cont = model_did_cont.bse['exposure_x_post']
pval_did_cont = model_did_cont.pvalues['exposure_x_post']

print(f"\n  β₃ (Exposure × Post) = {beta_did_cont:.6f} (SE: {se_did_cont:.6f}, p = {pval_did_cont:.6f})")
print(f"  Interpretation: 10pp increase in AI exposure → {beta_did_cont*0.1*100:.2f}% additional wage change")

# =============================================================================
# STEP 7: Quartile Analysis
# =============================================================================
print("\n" + "=" * 80)
print("STEP 7: Quartile Analysis (Q4 vs Q1)")
print("=" * 80)

# Compare top vs bottom quartile
quartile_summary = []
for period, col in [('Pre (2022-2023)', 'delta_ln_wage_pre'),
                     ('Post (2023-2024)', 'delta_ln_wage_post')]:
    q1_mean = panel_data[panel_data['exposure_quartile'] == 'Q1'][col].mean()
    q4_mean = panel_data[panel_data['exposure_quartile'] == 'Q4'][col].mean()
    quartile_summary.append({
        'Period': period,
        'Q1 (Low Exposure)': q1_mean,
        'Q4 (High Exposure)': q4_mean,
        'Difference (Q4 - Q1)': q4_mean - q1_mean
    })

quartile_df = pd.DataFrame(quartile_summary)
print("\n", quartile_df.to_string(index=False))

q_did = quartile_df.loc[1, 'Difference (Q4 - Q1)'] - quartile_df.loc[0, 'Difference (Q4 - Q1)']
print(f"\nDiff-in-Diff (Q4 vs Q1): {q_did:.4f}")
if q_did < 0:
    print(f"  → Top quartile experienced {abs(q_did)*100:.2f}% additional decline vs bottom quartile")
else:
    print(f"  → Top quartile experienced {q_did*100:.2f}% relative gain vs bottom quartile")

# =============================================================================
# STEP 8: Parallel Trends Test (Placebo)
# =============================================================================
print("\n" + "=" * 80)
print("STEP 8: Parallel Trends Assumption")
print("=" * 80)

print("\nCRITICAL ASSUMPTION: High and low exposure groups would have had similar")
print("wage growth trends in absence of LLM treatment.")
print()
print("TEST: Are pre-period trends similar? (they should be for valid DiD)")

pre_diff = pre_high - pre_low
print(f"\nPre-period difference (High - Low): {pre_diff:.4f}")

if abs(pre_diff) < 0.01:
    print("  ✓ Parallel trends assumption LIKELY SATISFIED (difference < 1%)")
else:
    print(f"  ⚠️  WARNING: Pre-existing differential trend of {pre_diff*100:.2f}%")
    print("     DiD estimate may be biased if pre-trends diverge")

# =============================================================================
# STEP 9: Visualizations
# =============================================================================
print("\n" + "=" * 80)
print("STEP 9: Creating visualizations...")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Parallel trends plot
ax1 = axes[0, 0]
periods = ['2022-2023', '2023-2024']
high_means = [pre_high, post_high]
low_means = [pre_low, post_low]

ax1.plot(periods, high_means, 'o-', linewidth=2, markersize=8, label='High Exposure', color='#d62728')
ax1.plot(periods, low_means, 'o-', linewidth=2, markersize=8, label='Low Exposure', color='#2ca02c')
ax1.axvline(0.5, color='gray', linestyle='--', alpha=0.5, label='LLM Release (Mar 2023)')
ax1.set_xlabel('Period')
ax1.set_ylabel('Mean Δln(Wage)')
ax1.set_title('Parallel Trends: High vs Low Exposure')
ax1.legend()
ax1.grid(alpha=0.3)

# 2. Diff-in-diff bar chart
ax2 = axes[0, 1]
x = np.arange(2)
width = 0.35
ax2.bar(x - width/2, [pre_high, post_high], width, label='High Exposure', color='#d62728')
ax2.bar(x + width/2, [pre_low, post_low], width, label='Low Exposure', color='#2ca02c')
ax2.set_ylabel('Mean Δln(Wage)')
ax2.set_title('Wage Growth by Period and Exposure')
ax2.set_xticks(x)
ax2.set_xticklabels(['Pre (2022-23)', 'Post (2023-24)'])
ax2.legend()
ax2.grid(alpha=0.3, axis='y')

# 3. Exposure distribution
ax3 = axes[1, 0]
ax3.hist(panel_data['ai_exposure'], bins=30, alpha=0.7, edgecolor='black')
ax3.axvline(median_exposure, color='r', linestyle='--', linewidth=2,
            label=f'Median: {median_exposure:.3f}')
ax3.set_xlabel('AI Exposure')
ax3.set_ylabel('Frequency')
ax3.set_title('Distribution of AI Exposure')
ax3.legend()
ax3.grid(alpha=0.3)

# 4. Scatterplot: Exposure vs Diff-in-Diff
ax4 = axes[1, 1]
panel_data['individual_did'] = panel_data['delta_ln_wage_post'] - panel_data['delta_ln_wage_pre']
ax4.scatter(panel_data['ai_exposure'], panel_data['individual_did'], alpha=0.5, s=50)
ax4.axhline(0, color='r', linestyle='--', linewidth=2)
# Add regression line
z = np.polyfit(panel_data['ai_exposure'], panel_data['individual_did'], 1)
p = np.poly1d(z)
x_plot = np.linspace(panel_data['ai_exposure'].min(), panel_data['ai_exposure'].max(), 100)
ax4.plot(x_plot, p(x_plot), 'r-', linewidth=2)
ax4.set_xlabel('AI Exposure')
ax4.set_ylabel('Individual DiD (Post - Pre)')
ax4.set_title('Exposure vs Change in Wage Growth')
ax4.grid(alpha=0.3)

plt.tight_layout()
fig_path = OUTPUT_DIR / 'did_analysis_plots.png'
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved plots to: {fig_path}")

# =============================================================================
# STEP 10: Save results
# =============================================================================
print("\n" + "=" * 80)
print("STEP 10: Saving results...")
print("=" * 80)

# Main results summary
results_summary = pd.DataFrame({
    'Specification': [
        'Simple DiD (Binary)',
        'Regression DiD (Binary)',
        'Regression DiD (Continuous)',
        'Quartile DiD (Q4 vs Q1)'
    ],
    'Estimate': [
        did_simple,
        beta_did,
        beta_did_cont,
        q_did
    ],
    'SE': [
        np.nan,
        se_did,
        se_did_cont,
        np.nan
    ],
    'P_value': [
        np.nan,
        pval_did,
        pval_did_cont,
        np.nan
    ],
    'Interpretation': [
        f"{did_simple*100:.2f}% additional change in high-exposure group",
        f"{beta_did*100:.2f}% additional change in high-exposure group",
        f"{beta_did_cont*0.1*100:.2f}% per 10pp exposure increase",
        f"{q_did*100:.2f}% Q4 vs Q1 difference"
    ]
})

results_summary.to_csv(OUTPUT_DIR / 'did_results_summary.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR / 'did_results_summary.csv'}")

# Detailed data
panel_data.to_csv(OUTPUT_DIR / 'did_panel_data.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR / 'did_panel_data.csv'}")

print("\n" + "=" * 80)
print("DIFF-IN-DIFF ANALYSIS COMPLETE")
print("=" * 80)

print("\n" + "=" * 80)
print("FINAL CONCLUSION")
print("=" * 80)

if pval_did < 0.05:
    if beta_did < 0:
        print(f"\n✓ CAUSAL EVIDENCE OF LLM DISPLACEMENT:")
        print(f"  - High-exposure occupations experienced {abs(beta_did)*100:.2f}% additional")
        print(f"    wage decline after LLM release (β₃ = {beta_did:.4f}, p < {pval_did:.3f})")
        print(f"  - Effect is statistically significant and economically meaningful")
    else:
        print(f"\n✓ NO DISPLACEMENT DETECTED:")
        print(f"  - High-exposure occupations experienced {beta_did*100:.2f}% relative GAIN")
        print(f"    (β₃ = {beta_did:.4f}, p < {pval_did:.3f})")
else:
    print(f"\n✗ NO CAUSAL EFFECT DETECTED:")
    print(f"  - Diff-in-diff coefficient: β₃ = {beta_did:.4f} (p = {pval_did:.3f})")
    print(f"  - High and low exposure groups show similar trends pre and post-LLM")
    print(f"  - Cannot reject null hypothesis of no LLM effect")

print(f"\nPre-existing trend difference: {(pre_high - pre_low)*100:.2f}%")
print(f"Post-LLM trend difference: {(post_high - post_low)*100:.2f}%")
print(f"Change (DiD): {did_simple*100:.2f}%")

print("\n" + "=" * 80)
