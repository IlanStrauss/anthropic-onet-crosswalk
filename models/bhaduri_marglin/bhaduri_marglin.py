"""
Bhaduri-Marglin Endogenous Regime Model (CORRECTED)
====================================================

Post-Keynesian model with investment responding to both capacity utilization
AND profit share. Endogenously determines wage-led vs profit-led regime.

Investment function: I = g₀ + g_u×u + g_π×π
Equilibrium: u* = (g₀ + g_π×π) / (s_π×π - g_u)

CORRECTIONS based on ChatGPT feedback:
- Fixed missing columns (task_importance, job_zone vs Job Zone)
- Use first_nonnull to avoid false missingness
- Calibrate g₀ to hit baseline utilization
- Clarify ai_exposure is global share, not within-occupation intensity

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026 (corrected)
"""

import numpy as np
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
U_BASELINE = 0.80  # Baseline capacity utilization (80%)
WAGE_SHARE_BASELINE = 0.55  # Approximate US wage share


def first_nonnull(x):
    """Get first non-null value to avoid false missingness from 'first'."""
    x = x.dropna()
    return x.iloc[0] if len(x) else np.nan


def load_crosswalk():
    """Load crosswalk with BLS wage data."""
    return pd.read_csv(CROSSWALK_FILE)


def calculate_occupation_exposure(df):
    """
    Aggregate task-level data to occupation level.

    WARNING: This produces GLOBAL API usage share, not within-occupation exposure.
    ai_exposure = (API usage for occupation) / (total API usage across all occupations)
    """
    df = df.copy()

    # FIX: Handle column name variations
    if "Job Zone" in df.columns and "job_zone" not in df.columns:
        df = df.rename(columns={"Job Zone": "job_zone"})

    # FIX: task_importance not in attached CSV → set neutral placeholder
    if "task_importance" not in df.columns:
        df["task_importance"] = 1.0

    # FIX: nonroutine_total not in attached CSV → optional, skip if missing
    has_nonroutine = "nonroutine_total" in df.columns

    total_usage = df['api_usage_count'].sum()
    df['task_usage_share'] = df['api_usage_count'] / total_usage if total_usage > 0 else 0.0
    df['weighted_exposure'] = df['task_usage_share'] * df['task_importance'].fillna(df['task_importance'].mean())

    agg_dict = {
        'api_usage_count': 'sum',
        'task_usage_share': 'sum',  # This is occupation's share of ALL API usage (global)
        'weighted_exposure': 'sum',
        'A_MEAN': first_nonnull,  # FIX: Use first_nonnull, not 'first'
        'A_MEDIAN': first_nonnull,
        'TOT_EMP': first_nonnull,
        'onet_occupation_title': first_nonnull,
        'job_zone': first_nonnull,
        'task_importance': 'mean'
    }

    if has_nonroutine:
        agg_dict['nonroutine_total'] = 'mean'

    occ = df.groupby('onet_soc_code', as_index=False).agg(agg_dict)

    # CLARIFY: This is global usage share, not occupation-specific exposure intensity
    occ['occupation_usage_share_global'] = occ['task_usage_share']
    occ['ai_exposure_proxy'] = occ['weighted_exposure']

    return occ.dropna(subset=['TOT_EMP', 'A_MEAN']).copy()


def bhaduri_marglin_model(occ):
    """
    Calibrate Bhaduri-Marglin endogenous regime model.

    Investment: I = g₀ + g_u×u + g_π×π
    Savings: S = s_π × π × u
    Equilibrium: u* = (g₀ + g_π×π) / (s_π×π - g_u)

    FIX: Calibrate g₀ so u_star_before == U_BASELINE (not hardcoded G_0).
    """
    # Calculate wage bill
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()

    # Wage at risk (WARNING: using global usage share as proxy for displacement share)
    occ['wage_at_risk'] = occ['wage_bill'] * occ['ai_exposure_proxy']

    # Profit share calculations
    profit_share_baseline = 1 - WAGE_SHARE_BASELINE
    delta_profit_share = occ['wage_at_risk'].sum() / total_wage_bill if total_wage_bill > 0 else 0.0

    # FIX: Bound profit share to [0, 1]
    profit_share_new = np.clip(profit_share_baseline + delta_profit_share, 0.0, 1.0)

    # FIX: Calibrate g₀ so that u_star_before == U_BASELINE
    denom_before = (S_PI * profit_share_baseline) - G_U
    if denom_before <= 0:
        raise ValueError(f"Baseline denominator {denom_before:.4f} <= 0; cannot calibrate g₀ with these params.")

    G_0_calibrated = U_BASELINE * denom_before - (G_PI * profit_share_baseline)

    # Equilibrium utilization BEFORE AI shock (should equal U_BASELINE by construction)
    u_star_before = U_BASELINE

    # Equilibrium utilization AFTER AI shock
    denominator_after = (S_PI * profit_share_new) - G_U
    if denominator_after <= 0:
        u_star_after = U_BASELINE  # Fallback
    else:
        u_star_after = (G_0_calibrated + G_PI * profit_share_new) / denominator_after

    # FIX: Bound utilization to [0, 1]
    u_star_after = float(np.clip(u_star_after, 0.0, 1.0))

    # Change in utilization
    delta_u = u_star_after - u_star_before

    # Regime determination: ∂u*/∂π
    # With positive params, this is always negative → always wage-led in this reduced model
    regime_numerator = -(G_PI * G_U + G_0_calibrated * S_PI)
    regime_denominator = denom_before ** 2 if denom_before > 0 else 1
    partial_u_partial_pi = regime_numerator / regime_denominator

    regime = "profit-led" if partial_u_partial_pi > 0 else "wage-led"

    # Output effect
    output_effect = delta_u / U_BASELINE if U_BASELINE > 0 else 0

    return {
        'g0_calibrated': G_0_calibrated,
        'profit_share_baseline': profit_share_baseline,
        'profit_share_new': profit_share_new,
        'delta_profit_share': delta_profit_share,
        'u_star_before': u_star_before,
        'u_star_after': u_star_after,
        'delta_utilization': delta_u,
        'partial_u_partial_pi': partial_u_partial_pi,
        'regime': regime,
        'output_effect': output_effect,
        'total_wage_bill': total_wage_bill,
        's_pi': S_PI,
        'g_u': G_U,
        'g_pi': G_PI,
        'u_baseline': U_BASELINE
    }, occ


def save_results(results, occ):
    """Save model results."""
    # Occupation-level exposure
    occ.to_csv(OUTPUT_DIR / "occupation_exposure.csv", index=False)

    # Model summary
    summary = pd.DataFrame({
        'Metric': [
            'g₀ (calibrated)',
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
            results['g0_calibrated'],
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
            f"{results['g0_calibrated']:.4f}",
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
        'Parameter': ['s_π', 'g_u', 'g_π', 'g₀ (calibrated)', 'u_baseline', 'wage_share_baseline'],
        'Value': [S_PI, G_U, G_PI, results['g0_calibrated'], U_BASELINE, WAGE_SHARE_BASELINE],
        'Description': [
            'Propensity to save out of profits',
            'Investment sensitivity to utilization',
            'Investment sensitivity to profit share',
            'Autonomous investment rate (calibrated to baseline)',
            'Baseline capacity utilization',
            'Baseline wage share'
        ]
    })
    params.to_csv(OUTPUT_DIR / "parameters.csv", index=False)

    print("\n" + "="*80)
    print("BHADURI-MARGLIN MODEL RESULTS")
    print("="*80)
    print(summary.to_string(index=False))
    print("\nNOTE: With these parameter signs (all positive), regime is always wage-led.")
    print("To get profit-led regimes, need fuller Bhaduri-Marglin demand closure")
    print("(consumption out of wages vs profits, net exports effects, etc.)")

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
