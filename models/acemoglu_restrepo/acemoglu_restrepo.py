"""
Acemoglu-Restrepo Task Displacement Model
==========================================

Neoclassical task-based framework for analyzing AI's labor market effects.
Key equation: Δln(w) = -[(σ-1)/σ] × task_displacement_share

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

# Model parameter
SIGMA = 1.5  # Elasticity of substitution between tasks


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


def acemoglu_restrepo_model(occ):
    """
    Estimate Acemoglu-Restrepo task displacement model.

    Δln(w) = -[(σ-1)/σ] × task_displacement_share
    """
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


def save_results(results, occ):
    """Save model results."""
    # Occupation-level exposure
    occ.to_csv(OUTPUT_DIR / "occupation_exposure.csv", index=False)

    # Model summary
    summary = pd.DataFrame({
        'Metric': [
            'Wage-weighted task displacement',
            f'Predicted wage effect (σ={SIGMA})',
            'Employment-weighted exposure',
            'Total wage bill ($)'
        ],
        'Value': [
            results['task_displacement_share'],
            results['wage_effect'],
            results['emp_weighted_exposure'],
            results['total_wage_bill']
        ],
        'Percent': [
            f"{results['task_displacement_share']*100:.2f}%",
            f"{results['wage_effect']*100:.2f}%",
            f"{results['emp_weighted_exposure']*100:.2f}%",
            f"${results['total_wage_bill']:,.0f}"
        ]
    })
    summary.to_csv(OUTPUT_DIR / "model_results.csv", index=False)
    return summary


def main():
    """Run Acemoglu-Restrepo model."""
    df = load_crosswalk()
    occ = calculate_occupation_exposure(df)
    results, occ = acemoglu_restrepo_model(occ)
    summary = save_results(results, occ)
    return results, summary


if __name__ == '__main__':
    main()
