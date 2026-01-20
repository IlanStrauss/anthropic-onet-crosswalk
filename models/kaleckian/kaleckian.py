"""
Kaleckian Wage Share / Aggregate Demand Model
=============================================

Post-Keynesian demand-side framework analyzing how AI-driven income
redistribution affects aggregate demand through consumption channels.

Key insight: c_w > c_π → wage share ↓ → consumption ↓ → AD ↓

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

# Model parameters (from literature: Stockhammer 2011, Onaran & Galanis 2014)
C_W = 0.80   # Marginal propensity to consume out of wages
C_PI = 0.40  # Marginal propensity to consume out of profits
AVG_C = 0.70 # Aggregate consumption propensity (for multiplier)


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


def kaleckian_model(occ):
    """
    Estimate Kaleckian wage share / aggregate demand model.

    C = c_w × W + c_π × Π
    ΔC = (c_w - c_π) × Δω
    ΔY = κ × ΔC where κ = 1/(1-c)
    """
    # Calculate wage bill
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()

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
        'total_wage_bill': total_wage_bill,
        'c_w': C_W,
        'c_pi': C_PI
    }, occ


def save_results(results, occ):
    """Save model results."""
    # Occupation-level exposure
    occ.to_csv(OUTPUT_DIR / "occupation_exposure.csv", index=False)

    # Model summary
    summary = pd.DataFrame({
        'Metric': [
            'Wage share reduction',
            'Consumption effect',
            f'Keynesian multiplier (c={AVG_C})',
            'AD effect (with multiplier)',
            'Employment share at risk',
            'Wage bill at risk ($)'
        ],
        'Value': [
            results['wage_share_effect'],
            results['consumption_effect'],
            results['multiplier'],
            results['ad_effect'],
            results['emp_share_at_risk'],
            results['wage_at_risk']
        ],
        'Percent': [
            f"{results['wage_share_effect']*100:.2f}%",
            f"{results['consumption_effect']*100:.2f}%",
            f"{results['multiplier']:.2f}",
            f"{results['ad_effect']*100:.2f}%",
            f"{results['emp_share_at_risk']*100:.2f}%",
            f"${results['wage_at_risk']:,.0f}"
        ]
    })
    summary.to_csv(OUTPUT_DIR / "model_results.csv", index=False)
    return summary


def main():
    """Run Kaleckian model."""
    df = load_crosswalk()
    occ = calculate_occupation_exposure(df)
    results, occ = kaleckian_model(occ)
    summary = save_results(results, occ)
    return results, summary


if __name__ == '__main__':
    main()
