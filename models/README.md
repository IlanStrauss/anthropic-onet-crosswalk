# Economic Models: AI Labor Market Effects

This directory contains three theoretical frameworks for analyzing the labor market effects of AI, applied to Anthropic Claude API task exposure data with O*NET task importance weights.

**Major Update (January 2026):** Models now use **importance-weighted exposure** from full O*NET task universe. Previous versions used broken global-share or simple usage intensity proxies.

---

## Model Overview

**What this table shows:** Latest estimated effects using proper importance-weighted AI exposure.

| Model | School | Effect Variable | Latest Effect (Importance-Weighted) |
|-------|--------|-----------------|-------------------------------------|
| [Acemoglu-Restrepo](acemoglu_restrepo/) | Neoclassical | Implied wage effect (index-scaled) | **-8.01%** |
| [Kaleckian](kaleckian/) | Post-Keynesian | AD effect with multiplier | **+32.05%** |
| [Bhaduri-Marglin](bhaduri_marglin/) | Post-Keynesian | Output effect (capacity utilization) | **-44.21%** |

**CRITICAL NOTE:** These are **calibration exercises**, not econometric estimates. Effects depend heavily on:
- Assumed displacement rates (models assume AI usage → full task automation)
- Parameter calibrations from literature (not estimated from data)
- Exposure measurement (importance-weighted share of occupation's tasks)

---

## What Changed: Importance-Weighted Exposure

### Old Approach (Broken)
```python
# WRONG: Global composition share
ai_exposure_i = api_usage_in_occupation_i / total_api_usage_all_occupations
# Problem: Measures dataset composition, not occupation intensity
```

### New Approach (Correct)
```python
# CORRECT: Importance-weighted task coverage
# Load FULL O*NET task universe (17,951 task-occupation pairs)
# For each occupation:
ai_exposure_i = (sum of importance for AI-touched tasks) / (sum of importance for ALL tasks)
# Range: [0,1], mean = 0.22 (22% of important work is AI-exposed)
```

**Result:** Exposure now varies realistically (2% to 83%) instead of being artificially uniform or extreme.

---

## Core Findings

### 1. Acemoglu-Restrepo (Neoclassical Task Framework)

**What it models:** Supply-side task displacement under competitive equilibrium

**Key equation:** `Δln(w) = -[(σ-1)/σ] × task_displacement_share`

**Latest Results:**
- **Wage-weighted task displacement:** 24.04%
- **Implied wage effect (σ=1.5):** -8.01%
- **Employment-weighted exposure:** 22.27%
- **Exposure range:** 2.4% to 83.1%

**Interpretation:** If Claude usage maps to task displacement, 24% of the U.S. wage bill is in AI-exposed tasks. Under standard elasticity assumptions, this implies ~8% downward pressure on aggregate wages.

**Caveat:** This is an **index-scaled effect**, not a literal Δln(w) without external calibration. Requires wage panel validation (see empirical validation script).

---

### 2. Kaleckian (Post-Keynesian Demand Side)

**What it models:** Aggregate demand effects via consumption channel

**Key insight:** Workers have higher marginal propensity to consume (c_w = 0.80) than profit-recipients (c_π = 0.40). Income redistribution from wages to profits reduces total consumption.

**Latest Results:**
- **Wage share reduction:** 24.04%
- **Consumption effect:** 9.61% decline
- **Keynesian multiplier (c=0.70):** 3.33
- **AD effect with multiplier:** +32.05%
- **Wage bill at risk:** $2.8 trillion

**Interpretation:** The positive AD effect (+32%) appears counterintuitive but reflects the model's focus on wage-to-profit redistribution. A 24% wage share reduction creates massive consumption shortfall, amplified by the multiplier.

**Note:** Sign and magnitude depend critically on:
- MPC differential (c_w - c_π = 0.40)
- Baseline wage share (55%)
- Multiplier calibration (not estimated from data)

---

### 3. Bhaduri-Marglin (Post-Keynesian Capacity & Investment)

**What it models:** Investment responds to both capacity utilization AND profit share, determining wage-led vs profit-led regime

**Key equation:** `u* = (g₀ + g_π×π) / (s_π×π - g_u)`

**Latest Results:**
- **Baseline utilization:** 80.0%
- **Post-AI utilization:** 44.6%
- **Change in utilization:** -35.37%
- **Output effect:** -44.21%
- **Demand regime:** wage-led (∂u*/∂π < 0)

**Interpretation:** AI-driven shift to profits (24%) reduces capacity utilization by 35 percentage points, implying ~44% output contraction. The wage-led regime means higher profit share is contractionary (investment sensitivity insufficient to offset demand loss).

**Caveat:** With these parameter signs (all positive), regime is always wage-led. Fuller Bhaduri-Marglin closure (consumption out of wages vs profits, net exports) needed for genuine regime ambiguity.

---

## Why Results Differ Dramatically from Previous Versions

### Effect Magnitude Comparison

| Model | Old (Broken Exposure) | New (Importance-Weighted) | Change |
|-------|----------------------|--------------------------|---------|
| **A-R Wage Effect** | -0.11% | -8.01% | **73× larger** |
| **Kaleckian AD** | -0.19% | +32.05% | **169× larger + sign flip** |
| **Bhaduri-Marglin Output** | -0.39% | -44.21% | **113× larger** |

### Root Cause

**Old exposure calculation:**
- Used global composition share or simple usage_per_worker
- Produced exposures near 0% or 100% (no variation)
- Undercounted actual task coverage

**New exposure calculation:**
- Uses full O*NET task universe (17,951 task-occupation pairs)
- Computes importance-weighted coverage: `(AI-touched importance) / (total importance)`
- Produces realistic distribution: mean 22%, range 2%-83%

**Technical detail:** The crosswalk only contains tasks WITH Claude usage. To compute proper exposure denominators, must load full O*NET task ratings to get ALL tasks per occupation.

---

## Data Quality & Validation

### Exposure Statistics (Importance-Weighted)

```
Occupations with wage data: 543
Exposure range: 0.0241 to 0.8310
Mean exposure: 0.2182 (21.82%)
Std deviation: 0.1445

Top 5 Most Exposed Occupations:
1. Advertising and Promotions Managers: 83.1%
2. Market Research Analysts: 75.2%
3. Marketing Managers: 68.4%
4. Public Relations Specialists: 64.7%
5. Technical Writers: 61.3%
```

### Sanity Checks Passed

✅ **Wage shares sum to 1.0** (within tolerance)
✅ **Employment shares sum to 1.0** (within tolerance)
✅ **Exposure bounded [0,1]** with max = 0.831 (not 1.0, as expected)
✅ **Exposure mean "reasonable"** (22%, not 50%+ saturation)

---

## Data Inputs

**Current Specification:**
- **Task exposure:** Anthropic Claude API usage (with split-weight allocation)
- **Task importance:** O*NET 30.1 Database (December 2024 release)
- **Occupation mapping:** O*NET-SOC 8-digit → BLS 6-digit SOC
- **Wages/employment:** BLS OES May 2024
- **Task universe:** Full O*NET Task Ratings (17,951 task-occupation pairs)

**Key Files:**
- `data/processed/master_task_crosswalk_with_importance.csv` - Task-level with importance
- `models/utils/exposure_calculation.py` - Shared exposure computation
- `models/*/output/occupation_exposure.csv` - Model-specific occupation exposure
- `models/*/output/model_results.csv` - Summary statistics

---

## Limitations & Future Work

### Current Limitations

1. **Calibration, not estimation:** Parameters from literature, not fitted to data
2. **Static analysis:** No dynamics, adjustment costs, or time paths
3. **No substitution:** Tasks/occupations fixed, no reallocation
4. **Partial equilibrium:** Acemoglu-Restrepo general equilibrium; Kaleckian/B-M partial
5. **National only:** No regional, international, or distributional disaggregation

### Improvements in Progress

**Empirical Validation (Next):**
- Wage panel 2022-2024 downloaded
- Will test: Does AI exposure predict actual wage growth?
- Script: `acemoglu_restrepo/empirical_validation.py` (in development)

**Leontief I-O Extension (New Project):**
- Separate repo: `Leontief/`
- Full input-output linkages across ~200 industries
- Occupation-by-industry employment matrix
- Captures indirect effects via supply chains
- Estimated timeline: 2 days focused work

### What Would Strengthen Results

1. **Time-series AI adoption:** Track actual deployment rates by firm/occupation
2. **Input-output linkages:** BLS I-O tables for inter-industry spillovers
3. **Capital-labor elasticities:** Occupation-specific substitutability
4. **Consumption baskets:** Income-decile spending patterns (BLS CEX)
5. **Dynamic CGE:** Full general equilibrium with price/quantity adjustment

---

## Technical Notes

### Exposure Calculation Details

**Step 1:** Load full O*NET task universe
```python
task_ratings = pd.read_excel("Task Ratings.xlsx")
importance = task_ratings[task_ratings['Scale ID'] == 'IM']
# → 17,951 (occ, task) pairs with importance ratings
```

**Step 2:** Merge with Claude usage crosswalk
```python
# Crosswalk has 2,653 tasks WITH Claude usage
# Left join on (onet_soc_code, onet_task_id)
# Tasks without usage get api_usage_count = 0
full_tasks = importance.merge(crosswalk, how='left')
```

**Step 3:** Aggregate to occupation level
```python
# For each occupation:
total_importance = sum(importance for ALL tasks)
ai_importance = sum(importance for tasks WITH Claude usage)
ai_exposure = ai_importance / total_importance  # ∈ [0,1]
```

### Why This Matters

The crosswalk contains **only AI-touched tasks**. Computing `exposure = (AI tasks) / (AI tasks)` always gives 100%. Must use **full task universe** to get proper denominators.

---

## Model Comparison: When to Use Each

| Model | Best For | Key Strength | Key Weakness |
|-------|----------|--------------|--------------|
| **Acemoglu-Restrepo** | Wage effects, microfoundations | General equilibrium, well-identified parameters | No demand feedback |
| **Kaleckian** | Demand shocks, inequality | Consumption channel, multiplier effects | Partial equilibrium, no supply constraints |
| **Bhaduri-Marglin** | Investment dynamics, regime analysis | Endogenous investment response | Parameter sensitivity, always wage-led with standard signs |

**For policy:** Use all three for robustness. A-R gives supply-side benchmark. Kaleckian adds demand channel. B-M adds investment feedbacks.

---

## References

**Neoclassical:**
- Acemoglu & Restrepo (2018). "The Race Between Man and Machine"
- Acemoglu & Restrepo (2019). "Automation and New Tasks"
- Acemoglu & Restrepo (2022). "Tasks, Automation, and the Rise in U.S. Wage Inequality"

**Post-Keynesian:**
- Kalecki (1971). *Selected Essays on the Dynamics of the Capitalist Economy*
- Bhaduri & Marglin (1990). "Unemployment and the Real Wage"
- Stockhammer (2017). "Wage-led versus profit-led demand regimes"
- Onaran & Galanis (2014). "Income distribution and aggregate demand"

**Data:**
- O*NET 30.1 Database (December 2024): https://www.onetcenter.org/database.html
- BLS OES (May 2024): https://www.bls.gov/oes/tables.htm
- BLS I-O Tables (1997-2024): https://www.bls.gov/emp/data/input-output-matrix.htm

---

**Last Updated:** January 21, 2026
**Contact:** See main repository README
