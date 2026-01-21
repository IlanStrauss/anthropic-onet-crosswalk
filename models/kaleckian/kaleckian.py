"""
Kaleckian Wage Share / Aggregate Demand Model (CORRECTED)
==========================================================

Post-Keynesian demand-side framework analyzing how AI-driven income
redistribution affects aggregate demand through consumption channels.

Key insight: c_w > c_π → wage share ↓ → consumption ↓ → AD ↓

CORRECTIONS based on ChatGPT feedback:
- Replaced broken global-share exposure with usage_per_worker intensity
- Scale exposure to [0,1] via p99 cap (avoids outlier distortion)
- Simplified aggregation (no task_importance weighting)
- Use first_nonnull to avoid false missingness from 'first' aggregation

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

# Model parameters (from literature: Stockhammer 2011, Onaran & Galanis 2014)
C_W = 0.80   # Marginal propensity to consume out of wages
C_PI = 0.40  # Marginal propensity to consume out of profits
AVG_C = 0.70 # Aggregate consumption propensity (for multiplier)


def first_nonnull(x):
    """Get first non-null value to avoid false missingness from 'first'."""
    x = x.dropna()
    return x.iloc[0] if len(x) else np.nan


def load_crosswalk():
    """Load crosswalk with BLS wage data."""
    return pd.read_csv(CROSSWALK_FILE)


def calculate_occupation_exposure(df):
    """
    Build occupation-level table with proper exposure proxy.

    Exposure proxy: usage intensity per worker, scaled to [0,1] with p99 cap.
    This avoids broken task_importance weighting (not in CSV) and global share confusion.
    """
    # Occupation-level totals
    occ = df.groupby("onet_soc_code").agg(
        api_usage_count=("api_usage_count", "sum"),
        A_MEAN=("A_MEAN", first_nonnull),
        A_MEDIAN=("A_MEDIAN", first_nonnull),
        TOT_EMP=("TOT_EMP", first_nonnull),
        onet_occupation_title=("onet_occupation_title", first_nonnull),
        job_zone=("job_zone", first_nonnull)
    ).reset_index()

    # Drop rows missing key denominators
    occ = occ[occ["A_MEAN"].notna() & occ["TOT_EMP"].notna() & (occ["TOT_EMP"] > 0)].copy()

    # Exposure proxy: usage per worker, scaled to [0,1] with p99 cap
    occ["usage_per_worker"] = occ["api_usage_count"] / occ["TOT_EMP"]
    p99 = occ["usage_per_worker"].quantile(0.99)
    occ["ai_exposure"] = (occ["usage_per_worker"] / p99).clip(0, 1)

    return occ


def kaleckian_model(occ):
    """
    Estimate Kaleckian wage share / aggregate demand model.

    C = c_w × W + c_π × Π
    ΔC = (c_w - c_π) × Δω
    ΔY = κ × ΔC where κ = 1/(1-c)

    Uses usage_per_worker exposure proxy scaled to [0,1].
    """
    # Calculate wage bill
    occ = occ.copy()
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()

    # Wage bill at risk (exposure-weighted)
    occ['wage_at_risk'] = occ['wage_bill'] * occ['ai_exposure']
    wage_at_risk = occ['wage_at_risk'].sum()
    wage_share_effect = wage_at_risk / total_wage_bill if total_wage_bill > 0 else 0.0

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
        'emp_share_at_risk': emp_at_risk / total_emp if total_emp > 0 else 0.0,
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

    print("\n" + "="*80)
    print("KALECKIAN MODEL RESULTS")
    print("="*80)
    print(summary.to_string(index=False))
    print("\nNOTE: ai_exposure = usage_per_worker (scaled to [0,1] via p99 cap).")
    print("This is an occupation-level intensity proxy, not task-coverage or displacement share.")

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
