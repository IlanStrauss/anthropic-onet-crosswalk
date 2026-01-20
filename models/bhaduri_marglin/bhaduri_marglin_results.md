# Bhaduri-Marglin Endogenous Regime Model

## 1. Introduction & Motivation

The Bhaduri-Marglin (1990) model extends the Kaleckian framework by making **investment respond to profitability**. This allows the model to **endogenously determine** whether an economy is wage-led or profit-led.

**Why use this model?**

- **Investment matters**: Basic Kaleckian holds investment constant; B-M lets it respond to profits
- **Regime is endogenous**: Tests whether consumption or investment channel dominates
- **More complete**: Captures both demand-side (consumption) and supply-side (investment) channels
- **Policy-relevant**: Different regimes imply different optimal policies

**Key insight**: Higher profits can stimulate investment (profit-led channel) OR reduce consumption (wage-led channel). The **net effect** depends on parameter magnitudes.

**Key assumptions:**
- Investment responds to capacity utilization AND profit share
- Workers save a small fraction of wages (s_w = 0.08); capitalists save more (s_π = 0.45)
- Economy reaches goods market equilibrium
- Autonomous investment calibrated to hit baseline utilization (80%)

---

## 2. Model

### Core Equations

**Investment function:**
```
I = g₀ + g_u × u + g_π × π
```
Where:
- `g₀` = autonomous investment (calibrated to hit baseline u)
- `g_u` = sensitivity to capacity utilization (accelerator)
- `g_π` = sensitivity to profit share (profitability motive)
- `u` = capacity utilization
- `π` = profit share

**Savings function (with worker saving):**
```
S = [s_w × (1-π) + s_π × π] × u = σ × u
```
Where σ = aggregate saving propensity. Workers save s_w of wages; capitalists save s_π of profits.

**Equilibrium (I = S):**
```
u* = (g₀ + g_π × π) / (σ - g_u)
```
Where σ = s_w × (1-π) + s_π × π.

**Regime determination:**
```
∂u*/∂π > 0 → profit-led
∂u*/∂π < 0 → wage-led
```

The regime depends on whether higher profits raise saving (contractionary) more than they raise investment (expansionary). With s_w < s_π, higher π raises σ, which tends toward wage-led. With high g_π, higher π boosts investment, which tends toward profit-led.

### Mechanism

1. AI displaces wages → profit share rises (Δπ > 0)
2. **Investment channel**: Higher π stimulates investment (g_π × Δπ)
3. **Consumption channel**: Lower wages reduce consumption
4. **Net effect**: Depends on which channel dominates
5. If ∂u*/∂π < 0 → wage-led → output falls

---

## 3. Data & Methodology

### Variables from Our Data

| Variable | Description | Source |
|----------|-------------|--------|
| `api_usage_count` | API calls per task | Anthropic API logs |
| `ai_exposure` | Occupation-level AI exposure | Calculated |
| `TOT_EMP` | Employment per occupation | BLS OEWS |
| `A_MEAN` | Mean annual wage | BLS OEWS |
| `wage_bill` | `TOT_EMP × A_MEAN` | Calculated |
| `wage_at_risk` | `wage_bill × ai_exposure` | Calculated |
| `delta_profit_share` | `wage_at_risk / total_wage_bill` | Calculated |

### Parameters from Literature

| Parameter | Value | Description | Source |
|-----------|-------|-------------|--------|
| `s_w` | 0.08 | Saving propensity out of wages | Onaran & Galanis (2014): 0.05-0.15 |
| `s_π` | 0.45 | Saving propensity out of profits | Stockhammer (2017) |
| `g_u` | 0.10 | Investment sensitivity to utilization | Onaran & Galanis (2014) |
| `g_π` | 0.05 | Investment sensitivity to profit share | Stockhammer (2017) |
| `g₀` | 0.1166 | Autonomous investment rate | **Calibrated to u_baseline** |
| `u_baseline` | 0.80 | Baseline capacity utilization | Standard (80%) |
| `wage_share_baseline` | 0.55 | US wage share | BLS approximation |

**Parameter interpretation:**
- `s_w = 0.08`: Workers save 8% of wages
- `s_π = 0.45`: Capitalists save 45% of profits
- `g_u = 0.10`: 1% higher utilization → 0.1% more investment
- `g_π = 0.05`: 1pp higher profit share → 0.05% more investment
- `g₀ = 0.1166`: Calibrated so model hits u* = 0.80 at baseline profit share (0.45)

### Handling Ambiguous Task→SOC Mappings

Because O*NET task statements can be shared across multiple occupations, a subset of Anthropic task strings maps to multiple SOCs. We handle this as follows:

**Main specification (Equal-split):** When a task maps to N occupations, allocate 1/N of usage to each.

**Robustness check (Employment-weighted):** Allocate usage proportional to occupation employment.

| Metric | Value |
|--------|-------|
| Anthropic tasks with ambiguous mappings | 97 (4.6%) |
| API usage in ambiguous tasks | 7.9% |

### Calculation Steps

```
1. profit_share_baseline = 1 - wage_share_baseline = 0.45
2. wage_fraction_at_risk = wage_at_risk / total_wage_bill = 0.34%
3. delta_profit_share = wage_fraction_at_risk × wage_share_baseline = 0.34% × 0.55 = 0.18%
   (Converting from share of wages to share of total income)
4. profit_share_new = profit_share_baseline + delta_profit_share = 45.18%
5. σ_before = s_w × (1-π_before) + s_π × π_before
6. σ_after = s_w × (1-π_after) + s_π × π_after
7. u*_before = (g₀ + g_π × π_before) / (σ_before - g_u)
8. u*_after = (g₀ + g_π × π_after) / (σ_after - g_u)
9. delta_u = u*_after - u*_before
10. output_effect = delta_u / u_baseline
```

**Regime test (with worker saving):**

The regime depends on the sign of ∂u*/∂π. With worker saving included, the regime can genuinely flip between wage-led and profit-led depending on parameter values. At baseline parameters:
- Higher π raises σ (saving) because s_π > s_w → contractionary
- Higher π raises investment via g_π → expansionary
- Net effect depends on parameter magnitudes

---

## 4. Results

### Main Specification (Equal-Split Allocation)

| Metric | Value | Meaning |
|--------|-------|---------|
| **Baseline profit share** | 45.0% | Pre-AI profit share |
| **New profit share** | 45.18% | Post-AI profit share |
| **Change in profit share** | +0.18% | AI-driven redistribution (share of total income) |
| **Change in utilization** | -0.31% | Utilization decline |
| **Demand regime** | **WAGE-LED** | Consumption dominates investment |
| **Output effect** | -0.39% | Economy-wide output decline |
| **Occupations with wage data** | 558 | Coverage of US occupational structure |

### Robustness Check (Employment-Weighted Allocation)

| Metric | Equal-Split | Emp-Weighted | Difference |
|--------|-------------|--------------|------------|
| Change in profit share | 0.18% | 0.19% | +2.2% |
| Change in utilization | -0.31% | -0.32% | +2.3% |
| Output effect | -0.39% | -0.39% | +2.3% |
| Demand regime | Wage-led | Wage-led | Same |

**Interpretation:** Results are robust to the choice of allocation method for ambiguous tasks. The employment-weighted specification yields slightly higher estimates (+2.3%), but qualitative conclusions are unchanged. Both specifications confirm the economy is **wage-led**.

---

## 5. Results Interpretation

### What the -0.39% output effect means

- If AI-exposed wages were fully displaced to profits, **output would fall by 0.39%**
- This is **smaller than the Kaleckian effect** (-0.45%) because of model differences in multiplier channels
- The economy is confirmed to be **wage-led**: consumption loss > investment gain

### Comparison across models

| Model | Effect | Channels captured |
|-------|--------|-------------------|
| Acemoglu-Restrepo | -0.11% | Task displacement |
| Kaleckian | -0.45% | + Consumption + Keynesian multiplier |
| **Bhaduri-Marglin** | **-0.39%** | + Investment feedbacks (but different multiplier) |

**Note on B-M vs Kaleckian:** The B-M effect is slightly smaller because:
1. The B-M model uses a different equilibrium condition (I=S) than the Kaleckian multiplier
2. Investment response to profits partially offsets the consumption decline
3. Both models confirm wage-led regime, but with different equilibrium mechanisms

### Regime determination

**∂u*/∂π < 0** confirms:
- **Consumption channel dominates** investment channel
- US economy is **wage-led in demand**
- AI-driven profit share increase is **contractionary**

This aligns with empirical literature finding most advanced economies are wage-led.

### Policy implications

In a wage-led regime:
- **Redistributing to wages** boosts demand
- AI-driven wage displacement is **macro-contractionary**
- Policy responses: progressive taxation, wage floors, profit-sharing, fiscal stabilization

### Caveats

| Caveat | Implication |
|--------|-------------|
| Parameters from literature | Not estimated from AI data |
| Static equilibrium | No adjustment dynamics |
| Closed economy | Ignores trade effects |
| Linear investment function | Real response may be non-linear |
| 100% displacement assumed | Actual displacement rate (α) is unknown |

### Stability condition

For stable equilibrium: `σ - g_u > 0` (where σ = s_w(1-π) + s_π×π)

With our parameters: `0.2465 - 0.10 = 0.1465 > 0` ✓

Keynesian stability holds: savings more responsive than investment.

---

## 6. Parameter Sensitivity Analysis

### How AI Could Shift Model Parameters

AI may not only displace tasks—it could also shift the structural parameters that determine economic dynamics:

| Parameter | Baseline | AI Could Raise If... | AI Could Lower If... |
|-----------|----------|---------------------|---------------------|
| `s_w` (worker saving) | 0.08 | Precarity/gig economy raises saving | Wealth effects reduce saving |
| `s_π` (profit saving) | 0.45 | Tech firms retain earnings for R&D | More dividends/buybacks |
| `g_u` (accelerator) | 0.10 | AI makes investment more responsive | Uncertainty delays investment |
| `g_π` (profit sensitivity) | 0.05 | Profits strongly signal investment opportunities | Profits don't translate to investment |

### Scenario Results

**What this table shows:** How ΔY/Y (change in aggregate output/GDP) and the demand regime vary with saving (s_w, s_π) and investment (g_u, g_π) parameters.

| Scenario | Parameters | ΔY/Y (output change) | Demand Regime |
|----------|------------|----------------------|---------------|
| **Baseline (with worker saving)** | s_w=0.08, s_π=0.45, g_u=0.10, g_π=0.05 | **-0.39%** | wage-led |
| Lower worker saving (s_w=0.05) | s_w=0.05 | -0.48% | wage-led |
| Higher worker saving (s_w=0.15) | s_w=0.15 | -0.24% | wage-led |
| AI raises profit saving (s_π=0.55) | s_π=0.55 | -0.39% | wage-led |
| AI lowers profit saving (s_π=0.35) | s_π=0.35 | -0.38% | wage-led |
| AI boosts investment response (g_π=0.10) | g_π=0.10 | -0.31% | wage-led |
| Strong investment response (g_π=0.15) | g_π=0.15 | -0.23% | wage-led |
| Weaker accelerator (g_u=0.05) | g_u=0.05 | -0.29% | wage-led |
| Stronger accelerator (g_u=0.15) | g_u=0.15 | -0.58% | wage-led |
| Profit-led shift attempt | s_w=0.05, s_π=0.55, g_u=0.08, g_π=0.12 | -0.33% | wage-led |
| Wage-led intensification | s_w=0.15, s_π=0.35, g_u=0.12, g_π=0.03 | -0.25% | wage-led |

*Regime: wage-led = ∂u*/∂π < 0 (higher profit share reduces equilibrium capacity utilization)*

### Key Finding: Robust Wage-Led Regime

**All 11 scenarios remain wage-led.** Even aggressive parameter shifts toward profit-led dynamics (high g_π, low s_w, high s_π) do not flip the regime. This suggests:

1. The US economy is **wage-led** under standard Post-Keynesian parameter ranges
2. AI-driven redistribution is **contractionary across all tested scenarios**
3. Output effects range from **-0.23% to -0.58%** depending on parameters

### What Would Flip the Regime?

For profit-led demand, we would need investment response to profits (g_π) to dominate the saving differential (s_π - s_w). With our baseline gap of 0.37 (= 0.45 - 0.08), g_π would need to be implausibly high (≈0.20+) to overcome the contractionary saving effect.

### Best-Case Scenario (within wage-led)

If AI boosts investment response to profits (g_π=0.15):
- Output falls by only **0.23%**
- Investment partially offsets consumption decline

---

## 7. Model Comparison Summary

| Model | Effect | Range (Sensitivity) | Key Channel |
|-------|--------|---------------------|-------------|
| Acemoglu-Restrepo | -0.11% | 0% to -0.20% (vary σ) | Task displacement |
| Kaleckian | -0.45% | -0.23% to -0.45% (vary MPCs) | Consumption + multiplier |
| Bhaduri-Marglin | -0.39% | **-0.23% to -0.58%** (vary s_w, s_π, g_u, g_π) | Investment feedbacks |

**Key insight:** All three models show contractionary effects from AI-driven redistribution toward profits. The Bhaduri-Marglin model now includes worker saving (s_w) for genuinely endogenous regime determination and is internally consistent (g₀ calibrated to baseline utilization).

All models show **stable results** across allocation methods, with employment-weighted yielding slightly higher estimates (+2.2%).

---

## References

- Bhaduri, A., & Marglin, S. (1990). "Unemployment and the real wage." *Cambridge Journal of Economics*, 14(4), 375-393.
- Stockhammer, E. (2017). "Determinants of the Wage Share." *British Journal of Industrial Relations*, 55(1), 3-33.
- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.
- Blecker, R. A. (2016). "Wage-led versus profit-led demand regimes." *Review of Keynesian Economics*, 4(4), 373-390.
- Lavoie, M., & Stockhammer, E. (2013). *Wage-led Growth*. Palgrave Macmillan.
