# Economic Models: AI Labor Market Effects

This directory contains three theoretical frameworks for analyzing the labor market effects of AI, applied to Anthropic Claude API task exposure data.

**Important limitations:**
- Claude API usage measures **where Claude is used**, not tasks actually displaced
- Usage may reflect **complementarity** (productivity gains) as much as **substitution**
- All models assume 100% displacement (α=1) as a pessimistic upper bound

---

## Model Overview

| Model | School | Key Effect | Baseline Result |
|-------|--------|------------|-----------------|
| [Acemoglu-Restrepo](acemoglu_restrepo/) | Neoclassical | Wage (pessimistic) | **-0.11%** |
| [Kaleckian](kaleckian/) | Post-Keynesian | Aggregate demand | **-0.19%** |
| [Bhaduri-Marglin](bhaduri_marglin/) | Post-Keynesian | Output (with investment) | **-0.39%** |

---

## Core Findings

### 1. Acemoglu-Restrepo Inspired (Mainstream Benchmark)

**What it models:** Supply-side task displacement under full employment

**Key equation:** `Δln(w) = φ - [(σ-1)/σ] × α × exposure_share`

**Finding:** 0.34% of US wage bill is in AI-used tasks → **-0.11% wage effect** (under α=1, φ=0)

**Limitation:** Usage ≠ displacement; effect could be zero or positive if AI complements labor

---

### 2. Kaleckian (Post-Keynesian)

**What it models:** Aggregate demand effects of income redistribution

**Key insight:** Workers spend more than capitalists (c_w > c_π), so shifting income to profits reduces consumption

**Finding:** AI-driven wage displacement → **-0.19% AD effect** (1.7x larger than A-R)

**Corrections applied:**
- Δω correctly converts wage fraction to income share change
- Multiplier derived from class MPCs: κ ≈ 2.04 (not exogenous 3.33)

---

### 3. Bhaduri-Marglin (Post-Keynesian)

**What it models:** Endogenous regime determination (wage-led vs profit-led)

**Key insight:** Investment responds to both utilization AND profit share

**Finding:** US economy is **wage-led** → AI redistribution is contractionary → **-0.39% output effect**

**Corrections applied:**
- Worker saving (s_w=0.08) added for genuine regime determination
- g₀ calibrated to hit baseline utilization (80%)
- Delta profit share correctly converts wage fraction to income share

---

## Why Results Differ

```
Acemoglu-Restrepo: -0.11%  ← Supply-side only (pessimistic displacement)
Kaleckian:         -0.19%  ← + Consumption channel + derived multiplier
Bhaduri-Marglin:   -0.39%  ← + Investment feedbacks
```

All three models show contractionary effects under the assumed 100% displacement scenario.

---

## Parameter Sensitivity Analysis

AI could shift structural parameters, not just displace tasks. We test how results vary:

### Acemoglu-Restrepo: Elasticity of Substitution (σ)

| σ | Description | Wage Effect |
|---|-------------|-------------|
| 1.0 | Cobb-Douglas (displacement term vanishes) | 0.00% |
| **1.5** | **Baseline** | **-0.11%** |
| 2.5 | Higher substitutability | -0.20% |

### Kaleckian: Marginal Propensities to Consume

| Scenario | AD Effect | Derived κ |
|----------|-----------|-----------|
| Workers save more (precarity) | -0.13% | 1.85 |
| **Baseline** | **-0.19%** | **2.04** |
| AI concentrates profits in low-spending firms | -0.25% | 2.12 |

### Bhaduri-Marglin: Investment & Saving Parameters

| Scenario | Output Effect | Regime |
|----------|---------------|--------|
| Best case (high g_π) | -0.23% | wage-led |
| **Baseline** | **-0.39%** | **wage-led** |
| Worst case (strong accelerator) | -0.58% | wage-led |

### Key Finding: Robust Wage-Led Regime

**All 11 B-M scenarios remain wage-led.** With worker saving (s_w=0.08), the regime is genuinely endogenous, but parameter ranges within Post-Keynesian literature don't flip to profit-led.

---

## Effect Ranges Summary

| Model | Baseline | Min | Max | Key Driver |
|-------|----------|-----|-----|------------|
| Acemoglu-Restrepo | -0.11% | 0.00% | -0.20% | σ (substitutability) |
| Kaleckian | -0.19% | -0.13% | -0.25% | MPC differential |
| Bhaduri-Marglin | -0.39% | -0.23% | -0.58% | s_w, s_π, g_u, g_π |

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

**Neoclassical:**
- Acemoglu & Restrepo (2018, 2019, 2022)

**Post-Keynesian:**
- Kalecki (1971)
- Bhaduri & Marglin (1990)
- Stockhammer (2017)
- Onaran & Galanis (2014)

See individual model directories for full citations.
