# Economic Models: AI Labor Market Effects

This directory contains three theoretical frameworks for analyzing the labor market effects of AI, applied to Anthropic Claude API task exposure data.

---

## Model Overview

| Model | School | Key Effect | Baseline Result |
|-------|--------|------------|-----------------|
| [Acemoglu-Restrepo](acemoglu_restrepo/) | Neoclassical | Wage displacement | **-0.11%** |
| [Kaleckian](kaleckian/) | Post-Keynesian | Aggregate demand | **-0.45%** |
| [Bhaduri-Marglin](bhaduri_marglin/) | Post-Keynesian | Output (with investment) | **-0.73%** |

---

## Core Findings

### 1. Acemoglu-Restrepo (Mainstream)

**What it models:** Task displacement under full employment

**Key equation:** `Δln(w) = -[(σ-1)/σ] × task_displacement_share`

**Finding:** 0.34% of the US wage bill is in AI-exposed tasks → **-0.11% wage effect**

**Limitation:** Assumes workers instantly reallocate to new tasks (no unemployment)

---

### 2. Kaleckian (Heterodox)

**What it models:** Aggregate demand effects of income redistribution

**Key insight:** Workers spend more than capitalists (c_w > c_π), so shifting income to profits reduces consumption

**Finding:** AI-driven wage displacement → **-0.45% AD effect** (4x larger than A-R)

**Why larger:** Captures consumption channel + Keynesian multiplier (3.33x)

---

### 3. Bhaduri-Marglin (Heterodox)

**What it models:** Endogenous regime determination (wage-led vs profit-led)

**Key insight:** Investment responds to both utilization AND profit share

**Finding:** US economy is **wage-led** → AI redistribution is contractionary → **-0.73% output effect**

**Why largest:** Adds investment feedback loop on top of Kaleckian channels

---

## Why Results Differ

```
Acemoglu-Restrepo: -0.11%  ← Supply-side only (task reallocation)
         ↓ +0.34%
Kaleckian:         -0.45%  ← + Consumption reduction + multiplier
         ↓ +0.28%
Bhaduri-Marglin:   -0.73%  ← + Investment feedbacks
```

The **progressive amplification** from mainstream to heterodox models shows demand-side and investment channels are quantitatively important.

---

## Parameter Sensitivity Analysis

AI could shift structural parameters, not just displace tasks. We test how results vary:

### Acemoglu-Restrepo: Elasticity of Substitution (σ)

| σ | Description | Wage Effect |
|---|-------------|-------------|
| 1.0 | Cobb-Douglas | 0.00% |
| **1.5** | **Baseline** | **-0.11%** |
| 2.5 | AI raises substitutability | -0.20% |

### Kaleckian: Marginal Propensities to Consume

| Scenario | AD Effect |
|----------|-----------|
| Workers save more (precarity) | 0.23% |
| **Baseline** | **0.45%** |
| AI concentrates profits in low-spending firms | 0.39% |

### Bhaduri-Marglin: Investment & Saving Parameters

| Scenario | Output Effect | Regime |
|----------|---------------|--------|
| Best case (weak accelerator) | -0.29% | wage-led |
| **Baseline** | **-0.73%** | **wage-led** |
| Worst case (intensified wage-led) | -4.08% | wage-led |

### Key Finding: Robust Wage-Led Regime

**All 9 B-M scenarios remain wage-led.** Even aggressive parameter shifts toward profit-led dynamics don't flip the regime. The US economy appears deeply wage-led in its structural parameters.

---

## Effect Ranges Summary

| Model | Baseline | Min | Max | Key Driver |
|-------|----------|-----|-----|------------|
| Acemoglu-Restrepo | -0.11% | 0.00% | -0.20% | σ (substitutability) |
| Kaleckian | -0.45% | 0.23% | 0.45% | MPC differential |
| Bhaduri-Marglin | -0.73% | -0.29% | -4.08% | Investment parameters |

---

## Data Inputs

All models use the same underlying data:
- **Task exposure:** Anthropic Claude API usage (Nov 2025)
- **Occupation mapping:** O*NET task statements
- **Wages/employment:** BLS OEWS May 2024
- **Ambiguous task handling:** Equal-split allocation (main), employment-weighted (robustness)

See `data/analysis/` for output files:
- `occupation_ai_exposure_equal.csv` - Main specification
- `occupation_ai_exposure_empweighted.csv` - Robustness
- `model_summary.csv` - Results comparison
- `parameter_sensitivity.csv` - Full scenario analysis

---

## References

**Mainstream:**
- Acemoglu & Restrepo (2018, 2019, 2022)

**Post-Keynesian:**
- Kalecki (1971)
- Bhaduri & Marglin (1990)
- Stockhammer (2017)
- Onaran & Galanis (2014)

See individual model directories for full citations.
