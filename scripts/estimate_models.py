"""
Estimate AI Labor Market Effects: Mainstream & Heterodox Models
===============================================================

Two theoretical frameworks applied to Anthropic API task exposure data:

1. ACEMOGLU-RESTREPO: Task displacement model (neoclassical)
   - Assumes full employment, calculates wage effects from task reallocation
   - Key equation: Δln(w) = -[(σ-1)/σ] × displacement_share

2. KALECKIAN: Wage share / aggregate demand model (Post-Keynesian)
   - Allows unemployment, demand-constrained output
   - Key insight: wage share ↓ → consumption ↓ → AD ↓ (if wage-led)

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIGURATION ---
DATA_DIR = Path(__file__).parent.parent
CROSSWALK_FILE = DATA_DIR / "processed" / "master_task_crosswalk_with_wages.csv"
OUTPUT_DIR = DATA_DIR / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# Kaleckian parameters (from literature: Stockhammer 2011, Onaran & Galanis 2014)
C_W = 0.80   # Marginal propensity to consume out of wages
C_PI = 0.40  # Marginal propensity to consume out of profits
AVG_C = 0.70 # Aggregate consumption propensity (for multiplier)

# Acemoglu-Restrepo parameter
SIGMA = 1.5  # Elasticity of substitution between tasks


def load_crosswalk():
    """Load crosswalk with BLS wage data."""
    return pd.read_csv(CROSSWALK_FILE)


def calculate_occupation_exposure(df):
    """
    Aggregate task-level data to occupation level.
    Calculate AI exposure as share of total API usage.
    """
    total_usage = df['api_usage_count'].sum()
    df['task_usage_share'] = df['api_usage_count'] / total_usage

    # Weight by task importance (standard in labor economics)
    df['weighted_exposure'] = df['task_usage_share'] * df['task_importance'].fillna(df['task_importance'].mean())

    # Aggregate to occupation
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
    MAINSTREAM MODEL: Acemoglu-Restrepo Task Displacement

    Theory: Production uses continuum of tasks. AI automates some,
    creating displacement effect on labor demand.

    Δln(w) = -[(σ-1)/σ] × task_displacement_share

    Returns dict with key estimates.
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
    }


def kaleckian_model(occ, ar_results):
    """
    HETERODOX MODEL: Kaleckian Wage Share / Aggregate Demand

    Theory: Aggregate demand depends on income distribution.
    C = c_w × W + c_π × Π, where c_w > c_π (workers spend more)

    If wage share falls: consumption falls, AD falls (in wage-led regime).
    Multiplier amplifies the effect.

    Returns dict with key estimates.
    """
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
    }


def routine_analysis(occ):
    """
    Test whether AI follows traditional automation pattern.

    Traditional view (Autor et al. 2003): automation affects ROUTINE tasks.
    LLMs may reverse this by affecting NON-ROUTINE COGNITIVE tasks.
    """
    occ['routine_intensity'] = 1 - occ['nonroutine_total']
    valid = occ[occ['routine_intensity'].notna()]

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
    occ['wage_quintile'] = pd.qcut(occ['A_MEAN'], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
    return occ.groupby('wage_quintile', observed=True).agg({
        'ai_exposure': 'mean',
        'TOT_EMP': 'sum',
        'A_MEAN': 'mean',
        'wage_at_risk': 'sum'
    }).reset_index()


def save_results(occ, ar, kalecki, routine):
    """Save occupation-level data and model summary."""
    # Occupation-level file
    occ.to_csv(OUTPUT_DIR / "occupation_ai_exposure.csv", index=False)

    # Model summary
    summary = pd.DataFrame({
        'Model': ['Acemoglu-Restrepo', 'Acemoglu-Restrepo', 'Kaleckian', 'Kaleckian', 'Kaleckian'],
        'Metric': [
            'Wage-weighted task displacement',
            'Predicted wage effect (σ={})'.format(SIGMA),
            'Wage share reduction',
            'AD effect (wage-led, with multiplier)',
            'Employment share at risk'
        ],
        'Value': [
            ar['task_displacement_share'],
            ar['wage_effect'],
            kalecki['wage_share_effect'],
            kalecki['ad_effect'],
            kalecki['emp_share_at_risk']
        ],
        'Percent': [
            f"{ar['task_displacement_share']*100:.2f}%",
            f"{ar['wage_effect']*100:.2f}%",
            f"{kalecki['wage_share_effect']*100:.2f}%",
            f"{kalecki['ad_effect']*100:.2f}%",
            f"{kalecki['emp_share_at_risk']*100:.2f}%"
        ]
    })
    summary.to_csv(OUTPUT_DIR / "model_summary.csv", index=False)


def main():
    """Run all model estimations."""
    # Load and prepare data
    df = load_crosswalk()
    occ = calculate_occupation_exposure(df)

    # Estimate models
    ar_results = acemoglu_restrepo_model(occ)
    kalecki_results = kaleckian_model(occ, ar_results)
    routine_results = routine_analysis(occ)

    # Save
    save_results(occ, ar_results, kalecki_results, routine_results)

    return ar_results, kalecki_results, routine_results


if __name__ == '__main__':
    main()
