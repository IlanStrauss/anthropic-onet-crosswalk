"""
Acemoglu-Restrepo Task Displacement Model (WITH IMPORTANCE WEIGHTING)
======================================================================

Neoclassical task-based framework for analyzing AI's labor market effects.
Key equation: Δln(w) = -[(σ-1)/σ] × task_displacement_share

LATEST VERSION: Now uses O*NET task importance weights!
- Exposure = (importance of AI-touched tasks) / (total task importance)
- Proper "task displacement share" concept
- Ready for empirical validation with wage panel

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026 (with importance weighting)
"""

import sys
from pathlib import Path

# Add models/utils to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "models" / "utils"))

import numpy as np
import pandas as pd
from exposure_calculation import calculate_importance_weighted_exposure

# --- CONFIGURATION ---
DATA_DIR = ROOT_DIR / "data"
CROSSWALK_FILE = DATA_DIR / "processed" / "master_task_crosswalk_with_importance.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Model parameter
SIGMA = 1.5  # Elasticity of substitution between tasks


def load_crosswalk():
    """Load crosswalk with BLS wage data and O*NET task importance."""
    return pd.read_csv(CROSSWALK_FILE)


def acemoglu_restrepo_model(occ):
    """
    Estimate Acemoglu-Restrepo task displacement model.

    Δln(w) = -[(σ-1)/σ] × task_displacement_share

    Uses max-normalized usage_per_worker as exposure proxy.
    """
    occ = occ.copy()

    # Calculate wage bill and shares
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()
    occ['wage_share'] = occ['wage_bill'] / total_wage_bill
    occ['emp_share'] = occ['TOT_EMP'] / occ['TOT_EMP'].sum()

    # SANITY CHECK: Shares should sum to 1.0
    wage_share_sum = occ['wage_share'].sum()
    emp_share_sum = occ['emp_share'].sum()

    if abs(wage_share_sum - 1.0) > 0.01:
        print(f"⚠️  WARNING: wage_share sums to {wage_share_sum:.4f}, not 1.0")
    if abs(emp_share_sum - 1.0) > 0.01:
        print(f"⚠️  WARNING: emp_share sums to {emp_share_sum:.4f}, not 1.0")

    # SANITY CHECK: Exposure should be in [0,1] with max=1.0
    exposure_max = occ['ai_exposure'].max()
    exposure_mean = occ['ai_exposure'].mean()
    if abs(exposure_max - 1.0) > 0.001:
        print(f"⚠️  WARNING: ai_exposure max is {exposure_max:.4f}, not 1.0")

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
        'total_wage_bill': total_wage_bill,
        'exposure_max': exposure_max,
        'exposure_mean': exposure_mean
    }, occ


def save_results(results, occ):
    """Save model results."""
    # Occupation-level exposure
    occ.to_csv(OUTPUT_DIR / "occupation_exposure.csv", index=False)

    # Model summary
    summary = pd.DataFrame({
        'Metric': [
            'Wage-weighted task displacement',
            f'Implied wage effect (σ={SIGMA}, index-scaled)',
            'Employment-weighted exposure',
            'Exposure max (sanity check)',
            'Exposure mean',
            'Total wage bill ($)'
        ],
        'Value': [
            results['task_displacement_share'],
            results['wage_effect'],
            results['emp_weighted_exposure'],
            results['exposure_max'],
            results['exposure_mean'],
            results['total_wage_bill']
        ],
        'Formatted': [
            f"{results['task_displacement_share']*100:.2f}%",
            f"{results['wage_effect']*100:.2f}%",
            f"{results['emp_weighted_exposure']*100:.2f}%",
            f"{results['exposure_max']:.4f}",
            f"{results['exposure_mean']:.4f}",
            f"${results['total_wage_bill']:,.0f}"
        ]
    })
    summary.to_csv(OUTPUT_DIR / "model_results.csv", index=False)

    print("\n" + "="*80)
    print("ACEMOGLU-RESTREPO MODEL RESULTS")
    print("="*80)
    print(summary.to_string(index=False))
    print("\nNOTE: ai_exposure = (importance of AI-touched tasks) / (total task importance).")
    print("Wage effect is index-scaled; see empirical validation script for actual Δln(w) estimation.")

    return summary


def main():
    """Run Acemoglu-Restrepo model."""
    df = load_crosswalk()
    occ = calculate_importance_weighted_exposure(df)
    results, occ = acemoglu_restrepo_model(occ)
    summary = save_results(results, occ)
    return results, summary


if __name__ == '__main__':
    main()
