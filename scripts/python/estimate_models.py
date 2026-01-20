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
# NOTE: Multiplier is now derived from class MPCs and distribution (see kaleckian_model)

# Acemoglu-Restrepo parameters
SIGMA = 1.5  # Elasticity of substitution between tasks
# NOTE: Higher σ means tasks are MORE substitutable (easier to replace labor with capital)
# At σ=1 (Cobb-Douglas), task displacement has zero wage effect
# As σ→∞, wage effect approaches -exposure_share
ALPHA = 1.0  # Displacement rate: fraction of exposed wage bill actually displaced (0-1)
             # α=1.0 is pessimistic "full displacement" assumption
             # Claude usage may represent complementarity, not displacement
PHI = 0.0    # Productivity effect: offsetting productivity gains in remaining tasks
             # A-R framework includes both displacement (-) and productivity (+) effects
             # We set φ=0 as pessimistic case (no offsetting productivity gains)

# Bhaduri-Marglin parameters (from literature: Stockhammer 2017, Onaran & Galanis 2014)
# CORRECTED: Now includes worker saving (s_w) for genuine regime determination
S_W = 0.08   # Propensity to save out of wages (s_w) - Onaran & Galanis (2014): 0.05-0.15
S_PI = 0.45  # Propensity to save out of profits (s_π)
G_U = 0.10   # Investment sensitivity to capacity utilization (g_u)
G_PI = 0.05  # Investment sensitivity to profit share (g_π)
U_BASELINE = 0.80  # Baseline capacity utilization (80%)
WAGE_SHARE_BASELINE = 0.55  # US wage share (for profit share calculation)

# CALIBRATED: g_0 set to hit U_BASELINE at baseline profit share
# u* = (g_0 + g_π×π) / (σ(π) - g_u) where σ(π) = s_w×(1-π) + s_π×π
# Solving: g_0 = u_baseline × (σ(π_0) - g_u) - g_π × π_0
_PI_BASELINE = 1 - WAGE_SHARE_BASELINE  # 0.45
_SIGMA_BASELINE = S_W * WAGE_SHARE_BASELINE + S_PI * _PI_BASELINE  # Aggregate saving rate
G_0 = U_BASELINE * (_SIGMA_BASELINE - G_U) - G_PI * _PI_BASELINE  # Calibrated to hit u*=0.80


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
    MAINSTREAM BENCHMARK: Acemoglu-Restrepo Inspired Task Model

    IMPORTANT CAVEATS (per ChatGPT review):
    - This is a DIDACTIC REDUCED-FORM PROXY, not the exact A-R framework
    - Claude API usage measures WHERE Claude is used, not tasks DISPLACED to capital
    - Usage may reflect COMPLEMENTARITY (productivity gains) as much as SUBSTITUTION
    - True A-R has both: Net = Productivity Effect - Displacement Effect
    - We report φ=0 (no productivity gains) as PESSIMISTIC upper bound on displacement

    Our proxy equation:
        Δln(w) = φ - [(σ-1)/σ] × α × exposure_share

    Where:
        φ = productivity effect (set to 0, pessimistic)
        σ = elasticity of substitution (higher = more substitutable)
        α = displacement rate (fraction of exposed tasks actually displaced)
        exposure_share = wage-weighted AI usage exposure

    At σ=1 (Cobb-Douglas): displacement term vanishes (workers reallocate)
    As σ→∞: wage effect approaches -α × exposure_share

    Returns dict with key estimates.
    """
    occ = occ.copy()

    # Calculate wage bill and shares
    occ['wage_bill'] = occ['TOT_EMP'] * occ['A_MEAN']
    total_wage_bill = occ['wage_bill'].sum()
    occ['wage_share'] = occ['wage_bill'] / total_wage_bill
    occ['emp_share'] = occ['TOT_EMP'] / occ['TOT_EMP'].sum()

    # AI-usage-weighted exposure share (NOT displacement - Claude usage may be complementary)
    exposure_share = (occ['wage_share'] * occ['ai_exposure']).sum()

    # Employment-weighted exposure
    emp_weighted = (occ['emp_share'] * occ['ai_exposure']).sum()

    # Wage effect: Productivity - Displacement (with α and φ parameters)
    # Displacement term: -[(σ-1)/σ] × α × exposure
    # Productivity term: +φ × exposure (set to 0 as pessimistic case)
    displacement_effect = -((SIGMA - 1) / SIGMA) * ALPHA * exposure_share
    productivity_effect = PHI * exposure_share
    wage_effect = productivity_effect + displacement_effect

    return {
        'exposure_share': exposure_share,  # Renamed from task_displacement_share
        'task_displacement_share': exposure_share,  # Keep for backwards compat
        'emp_weighted_exposure': emp_weighted,
        'wage_effect': wage_effect,
        'displacement_effect': displacement_effect,
        'productivity_effect': productivity_effect,
        'sigma': SIGMA,
        'alpha': ALPHA,
        'phi': PHI,
        'total_wage_bill': total_wage_bill
    }, occ


def kaleckian_model(occ, ar_results):
    """
    HETERODOX MODEL: Kaleckian Wage Share / Aggregate Demand

    CORRECTED VERSION (per ChatGPT review):
    1. Δω is now correctly computed as wage_fraction × ω₀ (change in wage SHARE of income)
    2. Multiplier is derived from class MPCs: c = c_w×ω + c_π×(1-ω)
    3. Signs are consistent (negative AD effect = contractionary)

    Theory: Aggregate demand depends on income distribution.
    C = c_w × W + c_π × Π, where c_w > c_π (workers spend more)

    Model closure: Y = C(Y,ω) + I + G + NX
    - Closed economy (NX=0)
    - I, G held constant
    - This is a "demand-side stress test", not a regime identification

    Under the standard Post-Keynesian assumption c_w > c_π, redistribution from
    wages to profits reduces consumption and aggregate demand.

    Returns dict with key estimates.
    """
    occ = occ.copy()
    total_wage_bill = ar_results['total_wage_bill']

    # Wage bill at risk (exposure-weighted)
    occ['wage_at_risk'] = occ['wage_bill'] * occ['ai_exposure']
    wage_at_risk = occ['wage_at_risk'].sum()
    wage_fraction_at_risk = wage_at_risk / total_wage_bill  # Fraction of wages displaced

    # CORRECTED: Convert wage fraction to change in wage SHARE of income
    # Δω = -ω₀ × (wage_at_risk / W) = -ω₀ × wage_fraction_at_risk
    # (Negative because wages fall, profit share rises)
    delta_omega = -WAGE_SHARE_BASELINE * wage_fraction_at_risk

    # CORRECTED: Derive multiplier from class MPCs and distribution
    # Aggregate MPC: c = c_w × ω + c_π × (1-ω)
    aggregate_mpc = C_W * WAGE_SHARE_BASELINE + C_PI * (1 - WAGE_SHARE_BASELINE)
    multiplier = 1 / (1 - aggregate_mpc)  # ~2.04 with baseline parameters

    # Consumption effect: ΔC/Y = (c_w - c_π) × Δω
    # Note: since Δω is negative (wages fall), and (c_w - c_π) > 0,
    # consumption_effect is negative (contractionary)
    consumption_effect = (C_W - C_PI) * delta_omega

    # Total AD effect with multiplier (ΔY/Y)
    # Negative value means contractionary
    ad_effect = consumption_effect * multiplier

    # Employment at risk
    occ['emp_at_risk'] = occ['TOT_EMP'] * occ['ai_exposure']
    total_emp = occ['TOT_EMP'].sum()
    emp_at_risk = occ['emp_at_risk'].sum()

    return {
        'wage_at_risk': wage_at_risk,
        'wage_fraction_at_risk': wage_fraction_at_risk,  # For transparency
        'wage_share_effect': wage_fraction_at_risk,  # Keep for backwards compat (now correctly named)
        'delta_omega': delta_omega,  # CORRECTED: actual change in wage share of income
        'consumption_effect': consumption_effect,
        'multiplier': multiplier,
        'aggregate_mpc': aggregate_mpc,  # For transparency
        'ad_effect': ad_effect,  # Now negative for contractionary
        'emp_at_risk': emp_at_risk,
        'emp_share_at_risk': emp_at_risk / total_emp,
        'c_w': C_W,
        'c_pi': C_PI,
        'omega_baseline': WAGE_SHARE_BASELINE
    }, occ


def bhaduri_marglin_model(occ, ar_results):
    """
    HETERODOX MODEL: Bhaduri-Marglin Endogenous Regime Determination

    CORRECTED VERSION with three fixes per ChatGPT review:
    1. delta_profit_share now correctly converts wage fraction to income fraction
    2. g_0 calibrated so model's baseline u* = U_BASELINE (consistency)
    3. Worker saving (s_w > 0) added so regime is genuinely endogenous

    Investment function: I = g₀ + g_u×u + g_π×π
    Savings function: S = (s_w×ω + s_π×π) × u  where ω = 1-π (wage share)
                     = σ(π) × u  where σ(π) = s_w×(1-π) + s_π×π

    Equilibrium (I = S):
        u* = (g₀ + g_π×π) / (σ(π) - g_u)

    Regime determination:
        ∂u*/∂π = [g_π×(σ-g_u) - (g₀+g_π×π)×(s_π-s_w)] / (σ-g_u)²

        If s_π > s_w (capitalists save more), the sign is AMBIGUOUS:
        - profit-led if investment response dominates saving response
        - wage-led if saving response dominates investment response

    References:
        - Bhaduri & Marglin (1990) "Unemployment and the real wage"
        - Stockhammer (2017) "Determinants of the Wage Share"
        - Onaran & Galanis (2014) "Income distribution and growth"
        - Hein (2014) "Distribution and Growth after Keynes" Ch. 6

    Returns dict with key estimates.
    """
    total_wage_bill = ar_results['total_wage_bill']

    # Baseline distribution
    profit_share_baseline = 1 - WAGE_SHARE_BASELINE  # 0.45

    # CORRECTED: AI-induced change in profit share
    # wage_at_risk / wage_bill gives fraction of wages displaced
    # To get change in profit share (Π/Y), multiply by wage share (W/Y)
    # Because Δπ = Δ(Π/Y) = wage_at_risk/Y = (wage_at_risk/W) × (W/Y)
    wage_fraction_at_risk = occ['wage_at_risk'].sum() / total_wage_bill
    delta_profit_share = wage_fraction_at_risk * WAGE_SHARE_BASELINE  # CORRECTED
    profit_share_new = profit_share_baseline + delta_profit_share

    # Aggregate saving rate function: σ(π) = s_w×(1-π) + s_π×π
    def sigma(pi):
        return S_W * (1 - pi) + S_PI * pi

    sigma_before = sigma(profit_share_baseline)
    sigma_after = sigma(profit_share_new)

    # Equilibrium utilization BEFORE AI shock
    denominator_before = sigma_before - G_U
    if denominator_before <= 0:
        u_star_before = U_BASELINE  # Unstable/undefined
    else:
        u_star_before = (G_0 + G_PI * profit_share_baseline) / denominator_before

    # Equilibrium utilization AFTER AI shock
    denominator_after = sigma_after - G_U
    if denominator_after <= 0:
        u_star_after = U_BASELINE
    else:
        u_star_after = (G_0 + G_PI * profit_share_new) / denominator_after

    # Change in utilization
    delta_u = u_star_after - u_star_before

    # CORRECTED Regime determination with worker saving:
    # ∂u*/∂π = [g_π×(σ-g_u) - (g₀+g_π×π)×(s_π-s_w)] / (σ-g_u)²
    # The sign is now GENUINELY AMBIGUOUS (not mechanically wage-led)
    if denominator_before > 0:
        numerator = (G_PI * denominator_before -
                     (G_0 + G_PI * profit_share_baseline) * (S_PI - S_W))
        partial_u_partial_pi = numerator / (denominator_before ** 2)
    else:
        partial_u_partial_pi = 0

    regime = "profit-led" if partial_u_partial_pi > 0 else "wage-led"

    # Output effect (relative to baseline utilization)
    output_effect = delta_u / U_BASELINE if U_BASELINE > 0 else 0

    # Investment effect: ΔI = g_u×Δu + g_π×Δπ
    investment_effect = G_U * delta_u + G_PI * delta_profit_share

    # Savings effect: ΔS ≈ σ×Δu + u×Δσ where Δσ = (s_π-s_w)×Δπ
    delta_sigma = (S_PI - S_W) * delta_profit_share
    savings_effect = sigma_before * delta_u + U_BASELINE * delta_sigma

    return {
        'profit_share_baseline': profit_share_baseline,
        'profit_share_new': profit_share_new,
        'delta_profit_share': delta_profit_share,
        'wage_fraction_at_risk': wage_fraction_at_risk,  # For transparency
        'u_star_before': u_star_before,
        'u_star_after': u_star_after,
        'delta_utilization': delta_u,
        'partial_u_partial_pi': partial_u_partial_pi,
        'regime': regime,
        'output_effect': output_effect,
        'investment_effect': investment_effect,
        'savings_effect': savings_effect,
        's_w': S_W,
        's_pi': S_PI,
        'g_u': G_U,
        'g_pi': G_PI,
        'g_0': G_0,
        'sigma_baseline': sigma_before
    }


def parameter_sensitivity_analysis(occ, ar_results):
    """
    Run models across different parameter scenarios.

    AI could plausibly shift these parameters:
    - σ: Task substitutability may increase with AI
    - c_π: Tech firm profits may have different spending patterns
    - g_π: AI investment may be more/less responsive to profits
    - s_π: Tech firms may save more of profits

    Returns DataFrame with results across scenarios.
    """
    results = []
    total_wage_bill = ar_results['total_wage_bill']
    task_displacement = ar_results['task_displacement_share']

    # Baseline values
    wage_share_baseline = 0.55
    profit_share_baseline = 1 - wage_share_baseline
    delta_profit_share = (occ['wage_at_risk'].sum() / total_wage_bill)

    # =========================================================================
    # ACEMOGLU-RESTREPO: Vary σ (elasticity of substitution)
    # =========================================================================
    sigma_scenarios = [
        (1.0, "Low substitutability (σ=1.0)"),
        (1.25, "Moderate-low (σ=1.25)"),
        (1.5, "Baseline (σ=1.5)"),
        (2.0, "High substitutability (σ=2.0)"),
        (2.5, "Very high (σ=2.5) - AI makes tasks more substitutable"),
    ]

    for sigma, desc in sigma_scenarios:
        wage_effect = -((sigma - 1) / sigma) * task_displacement
        results.append({
            'Model': 'Acemoglu-Restrepo',
            'Scenario': desc,
            'Parameter_Changed': f'σ = {sigma}',
            'Wage_Effect': wage_effect,
            'AD_Effect': None,
            'Output_Effect': None,
            'Regime': 'N/A (full employment)'
        })

    # =========================================================================
    # KALECKIAN: Vary MPCs
    # CORRECTED: Use proper delta_omega and derived multiplier
    # =========================================================================
    # CORRECTED delta_omega = -ω₀ × wage_fraction_at_risk
    delta_omega = -wage_share_baseline * delta_profit_share  # Now negative (wages fall)

    kalecki_scenarios = [
        (0.80, 0.40, "Baseline (c_w=0.80, c_π=0.40)"),
        (0.80, 0.30, "AI concentrates profits in low-spending tech firms"),
        (0.70, 0.40, "Workers save more (precarity, gig economy)"),
        (0.75, 0.50, "Financialization: more shareholder payouts"),
        (0.85, 0.35, "Stronger wage-led: workers spend more, profits less"),
    ]

    for c_w, c_pi, desc in kalecki_scenarios:
        # Derived multiplier from class MPCs: c = c_w×ω + c_π×(1-ω)
        aggregate_mpc = wage_share_baseline * c_w + (1 - wage_share_baseline) * c_pi
        multiplier = 1 / (1 - aggregate_mpc)

        # Consumption effect with correct delta_omega (negative)
        consumption_effect = (c_w - c_pi) * delta_omega
        ad_effect = consumption_effect * multiplier  # Now negative (contractionary)

        results.append({
            'Model': 'Kaleckian',
            'Scenario': desc,
            'Parameter_Changed': f'c_w={c_w}, c_π={c_pi}',
            'Wage_Effect': None,
            'AD_Effect': ad_effect,
            'Output_Effect': None,
            'Regime': 'wage-led' if c_w > c_pi else 'profit-led'
        })

    # =========================================================================
    # BHADURI-MARGLIN: Vary investment/saving parameters
    # CORRECTED: Now with worker saving (s_w) for genuine regime determination
    # =========================================================================
    # CORRECTED: delta_profit_share = wage_fraction × wage_share
    delta_profit_share_corrected = delta_profit_share * WAGE_SHARE_BASELINE

    bm_scenarios = [
        # (s_w, s_π, g_u, g_π, description)
        (0.08, 0.45, 0.10, 0.05, "Baseline (with worker saving)"),
        (0.05, 0.45, 0.10, 0.05, "Lower worker saving (s_w=0.05)"),
        (0.15, 0.45, 0.10, 0.05, "Higher worker saving (s_w=0.15)"),
        (0.08, 0.55, 0.10, 0.05, "AI raises profit saving (s_π=0.55)"),
        (0.08, 0.35, 0.10, 0.05, "AI lowers profit saving (s_π=0.35)"),
        (0.08, 0.45, 0.10, 0.10, "AI boosts investment response (g_π=0.10)"),
        (0.08, 0.45, 0.10, 0.15, "Strong investment response (g_π=0.15)"),
        (0.08, 0.45, 0.05, 0.05, "Weaker accelerator (g_u=0.05)"),
        (0.08, 0.45, 0.15, 0.05, "Stronger accelerator (g_u=0.15)"),
        (0.05, 0.55, 0.08, 0.12, "Profit-led shift attempt"),
        (0.15, 0.35, 0.12, 0.03, "Wage-led intensification"),
    ]

    for s_w, s_pi, g_u, g_pi, desc in bm_scenarios:
        # Aggregate saving rate: σ(π) = s_w×(1-π) + s_π×π
        def sigma(pi):
            return s_w * (1 - pi) + s_pi * pi

        sigma_before = sigma(profit_share_baseline)
        sigma_after = sigma(profit_share_baseline + delta_profit_share_corrected)

        # Calibrate g_0 to hit U_BASELINE at baseline
        g_0_cal = U_BASELINE * (sigma_before - g_u) - g_pi * profit_share_baseline

        # Equilibrium utilization BEFORE
        denom_before = sigma_before - g_u
        if denom_before <= 0:
            u_before = U_BASELINE
        else:
            u_before = (g_0_cal + g_pi * profit_share_baseline) / denom_before

        # Equilibrium utilization AFTER
        denom_after = sigma_after - g_u
        profit_share_new = profit_share_baseline + delta_profit_share_corrected
        if denom_after <= 0:
            u_after = U_BASELINE
        else:
            u_after = (g_0_cal + g_pi * profit_share_new) / denom_after

        delta_u = u_after - u_before
        output_effect = delta_u / U_BASELINE

        # CORRECTED Regime determination with worker saving:
        # ∂u*/∂π = [g_π×(σ-g_u) - (g₀+g_π×π)×(s_π-s_w)] / (σ-g_u)²
        if denom_before > 0:
            numerator = (g_pi * denom_before -
                        (g_0_cal + g_pi * profit_share_baseline) * (s_pi - s_w))
            partial = numerator / (denom_before ** 2)
            regime = "profit-led" if partial > 0 else "wage-led"
        else:
            regime = "unstable"

        results.append({
            'Model': 'Bhaduri-Marglin',
            'Scenario': desc,
            'Parameter_Changed': f's_w={s_w}, s_π={s_pi}, g_u={g_u}, g_π={g_pi}',
            'Wage_Effect': None,
            'AD_Effect': None,
            'Output_Effect': output_effect,
            'Regime': regime
        })

    return pd.DataFrame(results)


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

    # --- PARAMETER SENSITIVITY ANALYSIS ---
    print("\n=== Parameter Sensitivity Analysis ===")
    param_sensitivity = parameter_sensitivity_analysis(occ_equal, ar_equal)
    param_sensitivity.to_csv(OUTPUT_DIR / "parameter_sensitivity.csv", index=False)
    print(f"  - Saved: parameter_sensitivity.csv")

    # Print summary of regime shifts
    bm_scenarios = param_sensitivity[param_sensitivity['Model'] == 'Bhaduri-Marglin']
    wage_led = (bm_scenarios['Regime'] == 'wage-led').sum()
    profit_led = (bm_scenarios['Regime'] == 'profit-led').sum()
    print(f"  - B-M scenarios: {wage_led} wage-led, {profit_led} profit-led")

    # Range of effects
    ar_scenarios = param_sensitivity[param_sensitivity['Model'] == 'Acemoglu-Restrepo']
    print(f"  - A-R wage effect range: {ar_scenarios['Wage_Effect'].min()*100:.2f}% to {ar_scenarios['Wage_Effect'].max()*100:.2f}%")

    kalecki_scenarios = param_sensitivity[param_sensitivity['Model'] == 'Kaleckian']
    print(f"  - Kaleckian AD range: {kalecki_scenarios['AD_Effect'].min()*100:.2f}% to {kalecki_scenarios['AD_Effect'].max()*100:.2f}%")

    bm_output = bm_scenarios['Output_Effect'].dropna()
    print(f"  - B-M output range: {bm_output.min()*100:.2f}% to {bm_output.max()*100:.2f}%")

    return {
        'equal': {'ar': ar_equal, 'kalecki': kalecki_equal, 'bm': bm_equal, 'routine': routine_equal},
        'empweighted': {'ar': ar_emp, 'kalecki': kalecki_emp, 'bm': bm_emp, 'routine': routine_emp},
        'param_sensitivity': param_sensitivity
    }


if __name__ == '__main__':
    main()
