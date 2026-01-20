"""
Estimate AI Labor Market Effects: Mainstream & Heterodox Models
===============================================================

Three theoretical frameworks applied to Anthropic API task exposure data:

1. ACEMOGLU-RESTREPO: Task displacement model (neoclassical)
   - Assumes full employment, calculates wage effects from task reallocation
   - Key equation: Δln(w) = -[(σ-1)/σ] × displacement_share

2. KALECKIAN: Wage share / aggregate demand model (Post-Keynesian)
   - Allows unemployment, demand-constrained output
   - Key insight: wage share ↓ → consumption ↓ → AD ↓ (if wage-led)

3. BHADURI-MARGLIN: Endogenous regime determination (Post-Keynesian)
   - Investment responds to both utilization AND profit share
   - Determines whether economy is wage-led or profit-led
   - Key equation: I = g₀ + g_u×u + g_π×π

EXPOSURE SPECIFICATIONS:
- Main: Equal-split allocation for ambiguous task→SOC mappings
- Robustness: Employment-weighted allocation

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIGURATION ---
ROOT_DIR = Path(__file__).parent.parent.parent  # anthropic-onet-crosswalk/
DATA_DIR = ROOT_DIR / "data"
CROSSWALK_FILE = DATA_DIR / "processed" / "master_task_crosswalk_with_wages.csv"
OUTPUT_DIR = DATA_DIR / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# Kaleckian parameters (from literature: Stockhammer 2011, Onaran & Galanis 2014)
C_W = 0.80   # Marginal propensity to consume out of wages
C_PI = 0.40  # Marginal propensity to consume out of profits
AVG_C = 0.70 # Aggregate consumption propensity (for multiplier)

# Acemoglu-Restrepo parameter
SIGMA = 1.5  # Elasticity of substitution between tasks

# Bhaduri-Marglin parameters (from literature: Stockhammer 2017, Onaran & Galanis 2014)
S_PI = 0.45  # Propensity to save out of profits (s_π)
G_U = 0.10   # Investment sensitivity to capacity utilization (g_u)
G_PI = 0.05  # Investment sensitivity to profit share (g_π)
G_0 = 0.03   # Autonomous investment rate (g₀)
U_BASELINE = 0.80  # Baseline capacity utilization (80%)


def load_crosswalk():
    """Load crosswalk with BLS wage data."""
    return pd.read_csv(CROSSWALK_FILE)


def calculate_occupation_exposure_equal(df):
    """
    Aggregate task-level data to occupation level using EQUAL-SPLIT weights.
    This is the MAIN specification.

    The crosswalk already has api_usage_count split equally across ambiguous SOCs.
    """
    total_usage = df['api_usage_count'].sum()
    df = df.copy()
    df['task_usage_share'] = df['api_usage_count'] / total_usage

    # Weight by task importance (standard in labor economics)
    task_imp_mean = df['task_importance'].mean() if 'task_importance' in df.columns else 1.0
    if 'task_importance' in df.columns:
        df['weighted_exposure'] = df['task_usage_share'] * df['task_importance'].fillna(task_imp_mean)
    else:
        df['weighted_exposure'] = df['task_usage_share']

    # Aggregate to occupation
    agg_dict = {
        'api_usage_count': 'sum',
        'task_usage_share': 'sum',
        'weighted_exposure': 'sum',
        'A_MEAN': 'first',
        'A_MEDIAN': 'first',
        'TOT_EMP': 'first',
        'onet_occupation_title': 'first',
        'job_zone': 'first',
    }

    # Add optional columns if they exist
    if 'nonroutine_total' in df.columns:
        agg_dict['nonroutine_total'] = 'mean'
    if 'task_importance' in df.columns:
        agg_dict['task_importance'] = 'mean'

    occ = df.groupby('onet_soc_code').agg(agg_dict).reset_index()
    occ['ai_exposure'] = occ['task_usage_share']
    occ['weight_method'] = 'equal_split'

    return occ[occ['A_MEAN'].notna()].copy()


def calculate_occupation_exposure_empweighted(df):
    """
    Aggregate task-level data to occupation level using EMPLOYMENT-WEIGHTED splits.
    This is the ROBUSTNESS specification.

    For ambiguous tasks, re-weight based on occupation employment.
    """
    df = df.copy()

    # Get employment by SOC
    emp_by_soc = df.groupby('onet_soc_code')['TOT_EMP'].first().to_dict()

    # For each ambiguous group, recalculate weights based on employment
    if 'ambiguous_group_id' in df.columns and 'api_usage_count_original' in df.columns:
        # Process ambiguous groups
        ambig_mask = df['is_ambiguous'] == True
        if ambig_mask.any():
            for group_id in df.loc[ambig_mask, 'ambiguous_group_id'].unique():
                if pd.isna(group_id):
                    continue
                group_mask = df['ambiguous_group_id'] == group_id
                group_socs = df.loc[group_mask, 'onet_soc_code'].values
                group_emps = [emp_by_soc.get(soc, 0) for soc in group_socs]
                total_emp = sum(group_emps)

                if total_emp > 0:
                    # Employment-weighted split
                    original_usage = df.loc[group_mask, 'api_usage_count_original'].iloc[0]
                    for i, (idx, soc) in enumerate(zip(df.loc[group_mask].index, group_socs)):
                        emp_weight = group_emps[i] / total_emp
                        df.loc[idx, 'api_usage_count'] = original_usage * emp_weight
                        df.loc[idx, 'split_weight'] = emp_weight
                # If no employment data, keep equal split (fallback)

    total_usage = df['api_usage_count'].sum()
    df['task_usage_share'] = df['api_usage_count'] / total_usage

    # Weight by task importance
    task_imp_mean = df['task_importance'].mean() if 'task_importance' in df.columns else 1.0
    if 'task_importance' in df.columns:
        df['weighted_exposure'] = df['task_usage_share'] * df['task_importance'].fillna(task_imp_mean)
    else:
        df['weighted_exposure'] = df['task_usage_share']

    # Aggregate to occupation
    agg_dict = {
        'api_usage_count': 'sum',
        'task_usage_share': 'sum',
        'weighted_exposure': 'sum',
        'A_MEAN': 'first',
        'A_MEDIAN': 'first',
        'TOT_EMP': 'first',
        'onet_occupation_title': 'first',
        'job_zone': 'first',
    }

    if 'nonroutine_total' in df.columns:
        agg_dict['nonroutine_total'] = 'mean'
    if 'task_importance' in df.columns:
        agg_dict['task_importance'] = 'mean'

    occ = df.groupby('onet_soc_code').agg(agg_dict).reset_index()
    occ['ai_exposure'] = occ['task_usage_share']
    occ['weight_method'] = 'employment_weighted'

    return occ[occ['A_MEAN'].notna()].copy()


def acemoglu_restrepo_model(occ):
    """
    MAINSTREAM MODEL: Acemoglu-Restrepo Task Displacement

    Theory: Production uses continuum of tasks. AI automates some,
    creating displacement effect on labor demand.

    Δln(w) = -[(σ-1)/σ] × task_displacement_share

    Returns dict with key estimates.
    """
    occ = occ.copy()

    # Calculate wage bill and shares
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()
    occ['wage_share'] = occ['wage_bill'] / total_wage_bill
    occ['emp_share'] = occ['TOT_EMP'] / occ['TOT_EMP'].sum()

    # Task displacement share (wage-weighted)
    task_displacement = (occ['wage_share'] * occ['ai_exposure']).sum()

    # Employment-weighted exposure
    emp_weighted = (occ['emp_share'] * occ['ai_exposure']).sum()

    # Wage effect using A-R formula
    wage_effect = -((SIGMA - 1) / SIGMA) * task_displacement

    return {
        'task_displacement_share': task_displacement,
        'emp_weighted_exposure': emp_weighted,
        'wage_effect': wage_effect,
        'sigma': SIGMA,
        'total_wage_bill': total_wage_bill
    }, occ


def kaleckian_model(occ, ar_results):
    """
    HETERODOX MODEL: Kaleckian Wage Share / Aggregate Demand

    Theory: Aggregate demand depends on income distribution.
    C = c_w × W + c_π × Π, where c_w > c_π (workers spend more)

    If wage share falls: consumption falls, AD falls (in wage-led regime).
    Multiplier amplifies the effect.

    Returns dict with key estimates.
    """
    occ = occ.copy()
    total_wage_bill = ar_results['total_wage_bill']

    # Wage bill at risk (exposure-weighted)
    occ['wage_at_risk'] = occ['wage_bill'] * occ['ai_exposure']
    wage_at_risk = occ['wage_at_risk'].sum()
    wage_share_effect = wage_at_risk / total_wage_bill

    # Consumption effect: ΔC = (c_w - c_π) × Δω
    consumption_effect = (C_W - C_PI) * wage_share_effect

    # Keynesian multiplier: κ = 1/(1-c)
    multiplier = 1 / (1 - AVG_C)

    # Total AD effect with multiplier
    ad_effect = consumption_effect * multiplier

    # Employment at risk
    occ['emp_at_risk'] = occ['TOT_EMP'] * occ['ai_exposure']
    total_emp = occ['TOT_EMP'].sum()
    emp_at_risk = occ['emp_at_risk'].sum()

    return {
        'wage_at_risk': wage_at_risk,
        'wage_share_effect': wage_share_effect,
        'consumption_effect': consumption_effect,
        'multiplier': multiplier,
        'ad_effect': ad_effect,
        'emp_at_risk': emp_at_risk,
        'emp_share_at_risk': emp_at_risk / total_emp,
        'c_w': C_W,
        'c_pi': C_PI
    }, occ


def bhaduri_marglin_model(occ, ar_results):
    """
    HETERODOX MODEL: Bhaduri-Marglin Endogenous Regime Determination

    Theory: Investment responds to BOTH capacity utilization AND profit share.
    This allows endogenous determination of whether economy is wage-led or profit-led.

    Investment function: I = g₀ + g_u×u + g_π×π
    Savings function: S = s_π × π × u (Cambridge assumption: workers don't save)
    Equilibrium: I = S

    Solving for equilibrium utilization:
        u* = (g₀ + g_π×π) / (s_π×π - g_u)

    Regime determination:
        ∂u*/∂π > 0 → profit-led demand
        ∂u*/∂π < 0 → wage-led demand

    References:
        - Bhaduri & Marglin (1990) "Unemployment and the real wage"
        - Stockhammer (2017) "Determinants of the Wage Share"
        - Onaran & Galanis (2014) "Income distribution and growth"

    Returns dict with key estimates.
    """
    total_wage_bill = ar_results['total_wage_bill']

    # Current profit share (1 - wage share in our framework)
    wage_share_baseline = 0.55  # Approximate US wage share
    profit_share_baseline = 1 - wage_share_baseline

    # AI-induced change in profit share (wages displaced → profits)
    delta_profit_share = (occ['wage_at_risk'].sum() / total_wage_bill)
    profit_share_new = profit_share_baseline + delta_profit_share

    # Equilibrium utilization BEFORE AI shock
    denominator_before = (S_PI * profit_share_baseline) - G_U
    if denominator_before <= 0:
        u_star_before = U_BASELINE
    else:
        u_star_before = (G_0 + G_PI * profit_share_baseline) / denominator_before

    # Equilibrium utilization AFTER AI shock
    denominator_after = (S_PI * profit_share_new) - G_U
    if denominator_after <= 0:
        u_star_after = U_BASELINE
    else:
        u_star_after = (G_0 + G_PI * profit_share_new) / denominator_after

    # Change in utilization
    delta_u = u_star_after - u_star_before

    # Regime determination: ∂u*/∂π
    regime_numerator = -(G_PI * G_U + G_0 * S_PI)
    regime_denominator = denominator_before ** 2 if denominator_before > 0 else 1
    partial_u_partial_pi = regime_numerator / regime_denominator

    regime = "profit-led" if partial_u_partial_pi > 0 else "wage-led"

    # Output effect
    output_effect = delta_u / U_BASELINE if U_BASELINE > 0 else 0

    # Investment effect: ΔI = g_u×Δu + g_π×Δπ
    investment_effect = G_U * delta_u + G_PI * delta_profit_share

    # Savings effect: ΔS = s_π×(π×Δu + u×Δπ)
    savings_effect = S_PI * (profit_share_baseline * delta_u + U_BASELINE * delta_profit_share)

    return {
        'profit_share_baseline': profit_share_baseline,
        'profit_share_new': profit_share_new,
        'delta_profit_share': delta_profit_share,
        'u_star_before': u_star_before,
        'u_star_after': u_star_after,
        'delta_utilization': delta_u,
        'partial_u_partial_pi': partial_u_partial_pi,
        'regime': regime,
        'output_effect': output_effect,
        'investment_effect': investment_effect,
        'savings_effect': savings_effect,
        's_pi': S_PI,
        'g_u': G_U,
        'g_pi': G_PI,
        'g_0': G_0
    }


def routine_analysis(occ):
    """
    Test whether AI follows traditional automation pattern.

    Traditional view (Autor et al. 2003): automation affects ROUTINE tasks.
    LLMs may reverse this by affecting NON-ROUTINE COGNITIVE tasks.
    """
    if 'nonroutine_total' not in occ.columns:
        return {'correlation': np.nan, 'routine_mean_exposure': np.nan,
                'nonroutine_mean_exposure': np.nan, 'routine_mean_wage': np.nan,
                'nonroutine_mean_wage': np.nan}

    occ = occ.copy()
    occ['routine_intensity'] = 1 - occ['nonroutine_total']
    valid = occ[occ['routine_intensity'].notna()]

    if len(valid) == 0:
        return {'correlation': np.nan, 'routine_mean_exposure': np.nan,
                'nonroutine_mean_exposure': np.nan, 'routine_mean_wage': np.nan,
                'nonroutine_mean_wage': np.nan}

    correlation = valid['routine_intensity'].corr(valid['ai_exposure'])

    median_routine = valid['routine_intensity'].median()
    routine = valid[valid['routine_intensity'] >= median_routine]
    nonroutine = valid[valid['routine_intensity'] < median_routine]

    return {
        'correlation': correlation,
        'routine_mean_exposure': routine['ai_exposure'].mean(),
        'nonroutine_mean_exposure': nonroutine['ai_exposure'].mean(),
        'routine_mean_wage': routine['A_MEAN'].mean(),
        'nonroutine_mean_wage': nonroutine['A_MEAN'].mean()
    }


def distributional_analysis(occ):
    """Analyze AI exposure by wage quintile."""
    occ = occ.copy()
    occ['wage_quintile'] = pd.qcut(occ['A_MEAN'], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])

    agg_cols = {'ai_exposure': 'mean', 'TOT_EMP': 'sum', 'A_MEAN': 'mean'}
    if 'wage_at_risk' in occ.columns:
        agg_cols['wage_at_risk'] = 'sum'

    return occ.groupby('wage_quintile', observed=True).agg(agg_cols).reset_index()


def save_results(occ_equal, occ_emp, ar_equal, ar_emp, kalecki_equal, kalecki_emp,
                 bm_equal, bm_emp, routine_equal, routine_emp):
    """Save occupation-level data and model summary for both specifications."""

    # Occupation-level files
    occ_equal.to_csv(OUTPUT_DIR / "occupation_ai_exposure_equal.csv", index=False)
    occ_emp.to_csv(OUTPUT_DIR / "occupation_ai_exposure_empweighted.csv", index=False)

    # Model summary - comparing both specifications
    summary = pd.DataFrame({
        'Model': [
            'Acemoglu-Restrepo', 'Acemoglu-Restrepo',
            'Kaleckian', 'Kaleckian', 'Kaleckian',
            'Bhaduri-Marglin', 'Bhaduri-Marglin', 'Bhaduri-Marglin', 'Bhaduri-Marglin'
        ],
        'Metric': [
            'Wage-weighted task displacement',
            f'Predicted wage effect (σ={SIGMA})',
            'Wage share reduction',
            'AD effect (wage-led, with multiplier)',
            'Employment share at risk',
            'Change in profit share',
            'Change in capacity utilization',
            'Demand regime',
            'Output effect'
        ],
        'Equal_Split_Value': [
            ar_equal['task_displacement_share'],
            ar_equal['wage_effect'],
            kalecki_equal['wage_share_effect'],
            kalecki_equal['ad_effect'],
            kalecki_equal['emp_share_at_risk'],
            bm_equal['delta_profit_share'],
            bm_equal['delta_utilization'],
            bm_equal['regime'],
            bm_equal['output_effect']
        ],
        'Equal_Split_Pct': [
            f"{ar_equal['task_displacement_share']*100:.2f}%",
            f"{ar_equal['wage_effect']*100:.2f}%",
            f"{kalecki_equal['wage_share_effect']*100:.2f}%",
            f"{kalecki_equal['ad_effect']*100:.2f}%",
            f"{kalecki_equal['emp_share_at_risk']*100:.2f}%",
            f"{bm_equal['delta_profit_share']*100:.2f}%",
            f"{bm_equal['delta_utilization']*100:.2f}%",
            bm_equal['regime'],
            f"{bm_equal['output_effect']*100:.2f}%"
        ],
        'EmpWeighted_Value': [
            ar_emp['task_displacement_share'],
            ar_emp['wage_effect'],
            kalecki_emp['wage_share_effect'],
            kalecki_emp['ad_effect'],
            kalecki_emp['emp_share_at_risk'],
            bm_emp['delta_profit_share'],
            bm_emp['delta_utilization'],
            bm_emp['regime'],
            bm_emp['output_effect']
        ],
        'EmpWeighted_Pct': [
            f"{ar_emp['task_displacement_share']*100:.2f}%",
            f"{ar_emp['wage_effect']*100:.2f}%",
            f"{kalecki_emp['wage_share_effect']*100:.2f}%",
            f"{kalecki_emp['ad_effect']*100:.2f}%",
            f"{kalecki_emp['emp_share_at_risk']*100:.2f}%",
            f"{bm_emp['delta_profit_share']*100:.2f}%",
            f"{bm_emp['delta_utilization']*100:.2f}%",
            bm_emp['regime'],
            f"{bm_emp['output_effect']*100:.2f}%"
        ]
    })
    summary.to_csv(OUTPUT_DIR / "model_summary.csv", index=False)

    # Sensitivity comparison
    sensitivity = pd.DataFrame({
        'Metric': [
            'Task displacement share',
            'Wage effect',
            'Employment share at risk',
            'AD effect'
        ],
        'Equal_Split': [
            ar_equal['task_displacement_share'],
            ar_equal['wage_effect'],
            kalecki_equal['emp_share_at_risk'],
            kalecki_equal['ad_effect']
        ],
        'Emp_Weighted': [
            ar_emp['task_displacement_share'],
            ar_emp['wage_effect'],
            kalecki_emp['emp_share_at_risk'],
            kalecki_emp['ad_effect']
        ],
        'Pct_Difference': [
            100 * (ar_emp['task_displacement_share'] - ar_equal['task_displacement_share']) / ar_equal['task_displacement_share'] if ar_equal['task_displacement_share'] != 0 else 0,
            100 * (ar_emp['wage_effect'] - ar_equal['wage_effect']) / ar_equal['wage_effect'] if ar_equal['wage_effect'] != 0 else 0,
            100 * (kalecki_emp['emp_share_at_risk'] - kalecki_equal['emp_share_at_risk']) / kalecki_equal['emp_share_at_risk'] if kalecki_equal['emp_share_at_risk'] != 0 else 0,
            100 * (kalecki_emp['ad_effect'] - kalecki_equal['ad_effect']) / kalecki_equal['ad_effect'] if kalecki_equal['ad_effect'] != 0 else 0
        ]
    })
    sensitivity.to_csv(OUTPUT_DIR / "sensitivity_equal_vs_empweighted.csv", index=False)

    print(f"\nResults saved to {OUTPUT_DIR}/")
    print(f"  - occupation_ai_exposure_equal.csv (MAIN specification)")
    print(f"  - occupation_ai_exposure_empweighted.csv (robustness)")
    print(f"  - model_summary.csv")
    print(f"  - sensitivity_equal_vs_empweighted.csv")


def main():
    """Run all model estimations for both exposure specifications."""
    print("Loading crosswalk data...")
    df = load_crosswalk()

    # --- MAIN SPECIFICATION: Equal split ---
    print("\n=== MAIN SPECIFICATION: Equal-split allocation ===")
    occ_equal = calculate_occupation_exposure_equal(df)
    print(f"  - {len(occ_equal)} occupations with wage data")

    ar_equal, occ_equal = acemoglu_restrepo_model(occ_equal)
    kalecki_equal, occ_equal = kaleckian_model(occ_equal, ar_equal)
    bm_equal = bhaduri_marglin_model(occ_equal, ar_equal)
    routine_equal = routine_analysis(occ_equal)

    print(f"  - Task displacement: {ar_equal['task_displacement_share']*100:.2f}%")
    print(f"  - Wage effect: {ar_equal['wage_effect']*100:.2f}%")

    # --- ROBUSTNESS: Employment-weighted ---
    print("\n=== ROBUSTNESS: Employment-weighted allocation ===")
    occ_emp = calculate_occupation_exposure_empweighted(df)
    print(f"  - {len(occ_emp)} occupations with wage data")

    ar_emp, occ_emp = acemoglu_restrepo_model(occ_emp)
    kalecki_emp, occ_emp = kaleckian_model(occ_emp, ar_emp)
    bm_emp = bhaduri_marglin_model(occ_emp, ar_emp)
    routine_emp = routine_analysis(occ_emp)

    print(f"  - Task displacement: {ar_emp['task_displacement_share']*100:.2f}%")
    print(f"  - Wage effect: {ar_emp['wage_effect']*100:.2f}%")

    # --- Sensitivity comparison ---
    print("\n=== Sensitivity: Equal vs Employment-weighted ===")
    disp_diff = 100 * (ar_emp['task_displacement_share'] - ar_equal['task_displacement_share']) / ar_equal['task_displacement_share'] if ar_equal['task_displacement_share'] != 0 else 0
    print(f"  - Task displacement difference: {disp_diff:+.1f}%")

    # Save all results
    save_results(occ_equal, occ_emp, ar_equal, ar_emp, kalecki_equal, kalecki_emp,
                 bm_equal, bm_emp, routine_equal, routine_emp)

    return {
        'equal': {'ar': ar_equal, 'kalecki': kalecki_equal, 'bm': bm_equal, 'routine': routine_equal},
        'empweighted': {'ar': ar_emp, 'kalecki': kalecki_emp, 'bm': bm_emp, 'routine': routine_emp}
    }


if __name__ == '__main__':
    main()
