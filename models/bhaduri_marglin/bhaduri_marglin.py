"""
Bhaduri-Marglin Endogenous Regime Model
=======================================

Post-Keynesian model with investment responding to both capacity utilization
AND profit share. Endogenously determines wage-led vs profit-led regime.

Investment function: I = g₀ + g_u×u + g_π×π
Equilibrium: u* = (g₀ + g_π×π) / (s_π×π - g_u)

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import pandas as pd
from pathlib import Path

# --- CONFIGURATION ---
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CROSSWALK_FILE = DATA_DIR / "processed" / "master_task_crosswalk_with_wages.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Model parameters (from literature: Stockhammer 2017, Onaran & Galanis 2014)
S_PI = 0.45  # Propensity to save out of profits (s_π)
G_U = 0.10   # Investment sensitivity to capacity utilization (g_u)
G_PI = 0.05  # Investment sensitivity to profit share (g_π)
G_0 = 0.03   # Autonomous investment rate (g₀)
U_BASELINE = 0.80  # Baseline capacity utilization (80%)
WAGE_SHARE_BASELINE = 0.55  # Approximate US wage share


def load_crosswalk():
    """Load crosswalk with BLS wage data."""
    return pd.read_csv(CROSSWALK_FILE)


def calculate_occupation_exposure(df):
    """Aggregate task-level data to occupation level."""
    total_usage = df['api_usage_count'].sum()
    df['task_usage_share'] = df['api_usage_count'] / total_usage
    df['weighted_exposure'] = df['task_usage_share'] * df['task_importance'].fillna(df['task_importance'].mean())

    occ = df.groupby('onet_soc_code').agg({
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

    occ['ai_exposure'] = occ['task_usage_share']
    return occ[occ['A_MEAN'].notna()].copy()


def bhaduri_marglin_model(occ):
    """
    Estimate Bhaduri-Marglin endogenous regime model.

    Investment: I = g₀ + g_u×u + g_π×π
    Savings: S = s_π × π × u
    Equilibrium: u* = (g₀ + g_π×π) / (s_π×π - g_u)
    Regime: ∂u*/∂π ≷ 0 → profit-led / wage-led
    """
    # Calculate wage bill
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()

    # Wage at risk
    occ['wage_at_risk'] = occ['wage_bill'] * occ['ai_exposure']

    # Profit share calculations
    profit_share_baseline = 1 - WAGE_SHARE_BASELINE
    delta_profit_share = occ['wage_at_risk'].sum() / total_wage_bill
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
        'total_wage_bill': total_wage_bill,
        's_pi': S_PI,
        'g_u': G_U,
        'g_pi': G_PI,
        'g_0': G_0
    }, occ


def save_results(results, occ):
    """Save model results."""
    # Occupation-level exposure
    occ.to_csv(OUTPUT_DIR / "occupation_exposure.csv", index=False)

    # Model summary
    summary = pd.DataFrame({
        'Metric': [
            'Baseline profit share',
            'New profit share (post-AI)',
            'Change in profit share',
            'Equilibrium utilization (before)',
            'Equilibrium utilization (after)',
            'Change in utilization',
            'Demand regime',
            'Output effect',
            '∂u*/∂π (regime indicator)'
        ],
        'Value': [
            results['profit_share_baseline'],
            results['profit_share_new'],
            results['delta_profit_share'],
            results['u_star_before'],
            results['u_star_after'],
            results['delta_utilization'],
            results['regime'],
            results['output_effect'],
            results['partial_u_partial_pi']
        ],
        'Formatted': [
            f"{results['profit_share_baseline']*100:.1f}%",
            f"{results['profit_share_new']*100:.1f}%",
            f"{results['delta_profit_share']*100:.2f}%",
            f"{results['u_star_before']*100:.1f}%",
            f"{results['u_star_after']*100:.1f}%",
            f"{results['delta_utilization']*100:.2f}%",
            results['regime'],
            f"{results['output_effect']*100:.2f}%",
            f"{results['partial_u_partial_pi']:.4f}"
        ]
    })
    summary.to_csv(OUTPUT_DIR / "model_results.csv", index=False)

    # Parameters used
    params = pd.DataFrame({
        'Parameter': ['s_π', 'g_u', 'g_π', 'g₀', 'u_baseline', 'wage_share_baseline'],
        'Value': [S_PI, G_U, G_PI, G_0, U_BASELINE, WAGE_SHARE_BASELINE],
        'Description': [
            'Propensity to save out of profits',
            'Investment sensitivity to utilization',
            'Investment sensitivity to profit share',
            'Autonomous investment rate',
            'Baseline capacity utilization',
            'Baseline wage share'
        ]
    })
    params.to_csv(OUTPUT_DIR / "parameters.csv", index=False)

    return summary


def main():
    """Run Bhaduri-Marglin model."""
    df = load_crosswalk()
    occ = calculate_occupation_exposure(df)
    results, occ = bhaduri_marglin_model(occ)
    summary = save_results(results, occ)
    return results, summary


if __name__ == '__main__':
    main()
