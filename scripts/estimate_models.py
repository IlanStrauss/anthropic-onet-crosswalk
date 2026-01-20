#!/usr/bin/env python3
"""
Estimate Theoretical Models of AI Labor Market Effects
=======================================================

Two models estimated:

1. MAINSTREAM: Acemoglu-Restrepo Task Displacement Model
   Based on: Acemoglu & Restrepo (2018, 2019), Acemoglu (2025 NBER 33509)

2. HETERODOX: Kaleckian Wage Share / Aggregate Demand Model
   Based on: Kalecki (1954, 1971), Bhaduri-Marglin (1990), Stockhammer (2011)

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent
CROSSWALK_FILE = DATA_DIR / "processed" / "master_task_crosswalk_with_wages.csv"
OUTPUT_DIR = DATA_DIR / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("THEORETICAL MODELS OF AI LABOR MARKET EFFECTS")
print("=" * 70)


# =============================================================================
# LOAD DATA
# =============================================================================

print("\nLoading crosswalk data...")
df = pd.read_csv(CROSSWALK_FILE)
print(f"  Rows: {len(df):,}")
print(f"  Unique occupations: {df['onet_soc_code'].nunique()}")
print(f"  Total API usage: {df['api_usage_count'].sum():,.0f}")


# =============================================================================
# MODEL 1: ACEMOGLU-RESTREPO TASK DISPLACEMENT
# =============================================================================

print("\n" + "=" * 70)
print("MODEL 1: ACEMOGLU-RESTREPO TASK DISPLACEMENT")
print("=" * 70)

print("""
Theory (Acemoglu & Restrepo 2018, 2019; Acemoglu 2025):
-------------------------------------------------------
Production uses a continuum of tasks. AI automates some tasks,
creating a DISPLACEMENT EFFECT that reduces labor demand.

Key equation:
  Δln(w/r) = -[(σ-1)/σ] × [Task Displacement Share] + [Productivity Effect]

We estimate:
  1. Task Displacement Share by occupation
  2. Wage-weighted displacement
  3. Employment-weighted displacement
""")

# Calculate task-level exposure
# Following Acemoglu (2025 NBER 33509): exposure = f(AI usage, task importance)

# Normalize API usage to get task-level AI penetration
total_usage = df['api_usage_count'].sum()
df['task_usage_share'] = df['api_usage_count'] / total_usage

# Weight by task importance (standard in literature)
df['weighted_exposure'] = df['task_usage_share'] * df['task_importance'].fillna(df['task_importance'].mean())

# Aggregate to occupation level
occ_exposure = df.groupby('onet_soc_code').agg({
    'api_usage_count': 'sum',
    'task_usage_share': 'sum',
    'weighted_exposure': 'sum',
    'A_MEAN': 'first',
    'A_MEDIAN': 'first',
    'TOT_EMP': 'first',
    'onet_occupation_title': 'first',
    'Job Zone': 'first',
    'nonroutine_total': 'mean',
    'task_importance': 'mean'
}).reset_index()

# Calculate occupation-level AI exposure
occ_exposure['ai_exposure'] = occ_exposure['task_usage_share']

# Filter to occupations with wage data
occ_with_wages = occ_exposure[occ_exposure['A_MEAN'].notna()].copy()
print(f"\nOccupations with wage data: {len(occ_with_wages)}")

# TASK DISPLACEMENT SHARE CALCULATION
# Following Acemoglu-Restrepo: weight by wage bill (employment × wage)
occ_with_wages['wage_bill'] = occ_with_wages['TOT_EMP'] * occ_with_wages['A_MEAN']
total_wage_bill = occ_with_wages['wage_bill'].sum()
occ_with_wages['wage_share'] = occ_with_wages['wage_bill'] / total_wage_bill

# Task displacement share = sum of (wage_share × ai_exposure)
task_displacement_share = (occ_with_wages['wage_share'] * occ_with_wages['ai_exposure']).sum()

print(f"\n--- TASK DISPLACEMENT ESTIMATES ---")
print(f"Wage-weighted task displacement share: {task_displacement_share:.4f} ({task_displacement_share*100:.2f}%)")

# Employment-weighted exposure
occ_with_wages['emp_share'] = occ_with_wages['TOT_EMP'] / occ_with_wages['TOT_EMP'].sum()
emp_weighted_exposure = (occ_with_wages['emp_share'] * occ_with_wages['ai_exposure']).sum()
print(f"Employment-weighted AI exposure: {emp_weighted_exposure:.4f} ({emp_weighted_exposure*100:.2f}%)")

# Wage effect estimation
# Using simplified Acemoglu-Restrepo formula
# Assume σ = 1.5 (elasticity of substitution between tasks)
sigma = 1.5
displacement_effect = -((sigma - 1) / sigma) * task_displacement_share
print(f"\nPredicted wage effect (displacement only):")
print(f"  Assuming σ = {sigma}: Δln(w) = {displacement_effect:.4f} ({displacement_effect*100:.2f}%)")

# TOP EXPOSED OCCUPATIONS
print("\n--- TOP 20 AI-EXPOSED OCCUPATIONS (by wage-weighted exposure) ---")
top_exposed = occ_with_wages.nlargest(20, 'ai_exposure')[
    ['onet_occupation_title', 'ai_exposure', 'A_MEAN', 'TOT_EMP', 'Job Zone']
].copy()
top_exposed['A_MEAN'] = top_exposed['A_MEAN'].apply(lambda x: f"${x:,.0f}")
top_exposed['TOT_EMP'] = top_exposed['TOT_EMP'].apply(lambda x: f"{x:,.0f}")
top_exposed['ai_exposure'] = top_exposed['ai_exposure'].apply(lambda x: f"{x:.4f}")
print(top_exposed.to_string(index=False))

# BY JOB ZONE
print("\n--- AI EXPOSURE BY EDUCATION LEVEL (Job Zone) ---")
job_zone_exposure = occ_with_wages.groupby('Job Zone').agg({
    'ai_exposure': 'mean',
    'TOT_EMP': 'sum',
    'A_MEAN': 'mean'
}).reset_index()
job_zone_exposure['emp_pct'] = job_zone_exposure['TOT_EMP'] / job_zone_exposure['TOT_EMP'].sum() * 100
job_zone_labels = {
    1: 'No formal education',
    2: 'High school',
    3: 'Some college/vocational',
    4: "Bachelor's degree",
    5: 'Graduate degree'
}
job_zone_exposure['Education'] = job_zone_exposure['Job Zone'].map(job_zone_labels)
print(job_zone_exposure[['Job Zone', 'Education', 'ai_exposure', 'A_MEAN', 'emp_pct']].to_string(index=False))


# =============================================================================
# MODEL 2: KALECKIAN WAGE SHARE / AGGREGATE DEMAND
# =============================================================================

print("\n" + "=" * 70)
print("MODEL 2: KALECKIAN WAGE SHARE / AGGREGATE DEMAND")
print("=" * 70)

print("""
Theory (Kalecki 1954, 1971; Bhaduri-Marglin 1990):
--------------------------------------------------
Aggregate demand depends on functional income distribution:
  Y = C + I + G + NX
  C = c_w * W + c_π * Π   (where c_w > c_π)

If AI reduces wage share (W/Y ↓):
  - In WAGE-LED regime: AD ↓ → recession
  - In PROFIT-LED regime: AD may increase if I↑ offsets C↓

We estimate:
  1. Potential wage share effect of AI automation
  2. Aggregate demand impact under wage-led assumption
  3. Employment at risk
""")

# WAGE SHARE EFFECT CALCULATION
# Assume: if a task is AI-exposed, portion of wage bill at risk

# Method: Calculate wage bill in AI-exposed occupations
# Weight by exposure level

occ_with_wages['wage_at_risk'] = occ_with_wages['wage_bill'] * occ_with_wages['ai_exposure']
total_wage_at_risk = occ_with_wages['wage_at_risk'].sum()
wage_share_effect = total_wage_at_risk / total_wage_bill

print(f"\n--- WAGE SHARE ANALYSIS ---")
print(f"Total wage bill in sample: ${total_wage_bill/1e12:.2f} trillion")
print(f"Wage bill at risk (exposure-weighted): ${total_wage_at_risk/1e12:.4f} trillion")
print(f"Potential wage share reduction: {wage_share_effect:.4f} ({wage_share_effect*100:.2f}%)")

# AGGREGATE DEMAND EFFECT
# Kaleckian model: AD = C + I
# C = c_w * W + c_π * Π
# Standard estimates: c_w ≈ 0.8, c_π ≈ 0.4 (workers spend more of income)

c_w = 0.80  # Marginal propensity to consume out of wages
c_π = 0.40  # Marginal propensity to consume out of profits

# If wage share falls by Δω, demand effect depends on regime
# For wage-led economy: ∂Y/∂ω > 0

# Simplified calculation:
# ΔC = (c_w - c_π) * ΔW = (c_w - c_π) * wage_share_effect * Y
# Assuming Y normalized to 1

delta_consumption = (c_w - c_π) * wage_share_effect
print(f"\n--- AGGREGATE DEMAND EFFECT (Wage-Led Regime) ---")
print(f"Consumption propensity gap (c_w - c_π): {c_w - c_π:.2f}")
print(f"Direct consumption effect: Δ(C/Y) = {delta_consumption:.4f} ({delta_consumption*100:.2f}%)")

# Multiplier effect
# κ = 1 / (1 - c)  where c is aggregate propensity
# For wage-led: multiplier amplifies the effect
avg_c = 0.7  # Aggregate consumption propensity
multiplier = 1 / (1 - avg_c)
total_demand_effect = delta_consumption * multiplier

print(f"Keynesian multiplier (κ = 1/(1-c)): {multiplier:.2f}")
print(f"Total AD effect with multiplier: {total_demand_effect:.4f} ({total_demand_effect*100:.2f}%)")

# EMPLOYMENT AT RISK
# Method: Weight employment by AI exposure

occ_with_wages['emp_at_risk'] = occ_with_wages['TOT_EMP'] * occ_with_wages['ai_exposure']
total_emp = occ_with_wages['TOT_EMP'].sum()
total_emp_at_risk = occ_with_wages['emp_at_risk'].sum()

print(f"\n--- EMPLOYMENT AT RISK ---")
print(f"Total employment in sample: {total_emp:,.0f}")
print(f"Employment at risk (exposure-weighted): {total_emp_at_risk:,.0f}")
print(f"Share of employment at risk: {total_emp_at_risk/total_emp:.4f} ({total_emp_at_risk/total_emp*100:.2f}%)")

# DISTRIBUTIONAL ANALYSIS
# Following Kalecki: Who gains, who loses?

print("\n--- DISTRIBUTIONAL IMPACT BY WAGE QUINTILE ---")
occ_with_wages['wage_quintile'] = pd.qcut(occ_with_wages['A_MEAN'], 5, labels=['Q1 (lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (highest)'])
quintile_analysis = occ_with_wages.groupby('wage_quintile', observed=True).agg({
    'ai_exposure': 'mean',
    'TOT_EMP': 'sum',
    'A_MEAN': 'mean',
    'wage_at_risk': 'sum'
}).reset_index()
quintile_analysis['exposure_index'] = quintile_analysis['ai_exposure'] / quintile_analysis['ai_exposure'].mean()
print(quintile_analysis.to_string(index=False))


# =============================================================================
# COMPARISON: ROUTINE vs NON-ROUTINE TASKS
# =============================================================================

print("\n" + "=" * 70)
print("ROUTINE vs NON-ROUTINE TASK ANALYSIS")
print("=" * 70)

print("""
Following Autor, Levy & Murnane (2003), Autor & Dorn (2013):
------------------------------------------------------------
Traditional automation affects ROUTINE tasks (cognitive and manual).
LLMs may reverse this by affecting NON-ROUTINE COGNITIVE tasks.
""")

# Classify occupations by routine intensity
occ_with_wages['routine_intensity'] = 1 - occ_with_wages['nonroutine_total']

# Correlation between routine intensity and AI exposure
valid_routine = occ_with_wages[occ_with_wages['routine_intensity'].notna()]
corr = valid_routine['routine_intensity'].corr(valid_routine['ai_exposure'])
print(f"\nCorrelation: Routine intensity ↔ AI exposure: {corr:.3f}")

if corr > 0:
    print("  → AI (Claude) follows traditional automation pattern: MORE routine = MORE exposed")
else:
    print("  → AI (Claude) REVERSES traditional pattern: LESS routine = MORE exposed")
    print("  → Consistent with LLMs affecting non-routine cognitive tasks")

# Split by routine intensity
median_routine = valid_routine['routine_intensity'].median()
routine_jobs = valid_routine[valid_routine['routine_intensity'] >= median_routine]
nonroutine_jobs = valid_routine[valid_routine['routine_intensity'] < median_routine]

print(f"\n--- ROUTINE vs NON-ROUTINE COMPARISON ---")
print(f"{'Metric':<30} {'Routine Jobs':>15} {'Non-Routine Jobs':>18}")
print("-" * 65)
print(f"{'Number of occupations':<30} {len(routine_jobs):>15,} {len(nonroutine_jobs):>18,}")
print(f"{'Mean AI exposure':<30} {routine_jobs['ai_exposure'].mean():>15.4f} {nonroutine_jobs['ai_exposure'].mean():>18.4f}")
print(f"{'Mean wage':<30} ${routine_jobs['A_MEAN'].mean():>14,.0f} ${nonroutine_jobs['A_MEAN'].mean():>17,.0f}")
print(f"{'Total employment':<30} {routine_jobs['TOT_EMP'].sum():>15,.0f} {nonroutine_jobs['TOT_EMP'].sum():>18,.0f}")


# =============================================================================
# SAVE RESULTS
# =============================================================================

print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Save occupation-level analysis
occ_with_wages.to_csv(OUTPUT_DIR / "occupation_ai_exposure.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'occupation_ai_exposure.csv'}")

# Create summary statistics
summary = {
    'Model': ['Acemoglu-Restrepo', 'Acemoglu-Restrepo', 'Kaleckian', 'Kaleckian', 'Kaleckian'],
    'Metric': [
        'Wage-weighted task displacement share',
        'Predicted wage effect (σ=1.5)',
        'Potential wage share reduction',
        'Aggregate demand effect (wage-led)',
        'Employment share at risk'
    ],
    'Value': [
        f"{task_displacement_share:.4f}",
        f"{displacement_effect:.4f}",
        f"{wage_share_effect:.4f}",
        f"{total_demand_effect:.4f}",
        f"{total_emp_at_risk/total_emp:.4f}"
    ],
    'Percent': [
        f"{task_displacement_share*100:.2f}%",
        f"{displacement_effect*100:.2f}%",
        f"{wage_share_effect*100:.2f}%",
        f"{total_demand_effect*100:.2f}%",
        f"{total_emp_at_risk/total_emp*100:.2f}%"
    ]
}
summary_df = pd.DataFrame(summary)
summary_df.to_csv(OUTPUT_DIR / "model_summary.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'model_summary.csv'}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print("""
KEY FINDINGS:
-------------
1. MAINSTREAM (Acemoglu-Restrepo):
   - Task displacement from Claude API usage is concentrated in specific occupations
   - Wage effect depends on assumed elasticity of substitution (σ)

2. HETERODOX (Kaleckian):
   - AI-induced wage share reduction would reduce aggregate demand
   - Effect is amplified by Keynesian multiplier
   - Distributional impact varies across wage quintiles

CAVEATS:
--------
- Single AI product (Claude API only)
- One week of usage data
- Usage ≠ automation (task assistance, not replacement)
- Cross-sectional, no causal identification

REFERENCES:
-----------
- Acemoglu, D. (2025). "Artificial Intelligence and the Labor Market." NBER WP 33509.
- Acemoglu, D. & Restrepo, P. (2019). "Automation and New Tasks." JEP.
- Kalecki, M. (1954, 1971). Theory of Economic Dynamics.
- Autor, D. & Dorn, D. (2013). "Low-Skill Service Jobs." AER.
""")
