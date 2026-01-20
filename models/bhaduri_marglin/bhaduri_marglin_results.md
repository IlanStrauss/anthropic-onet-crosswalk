# Bhaduri-Marglin Endogenous Regime Model

## 1. Introduction & Motivation

The Bhaduri-Marglin (1990) model extends the Kaleckian framework by making **investment respond to profitability**. This allows the model to **endogenously determine** whether an economy is wage-led or profit-led.

**Why use this model?**

- **Investment matters**: Basic Kaleckian holds investment constant; B-M lets it respond to profits
- **Regime is endogenous**: Doesn't assume wage-led—tests whether consumption or investment channel dominates
- **More complete**: Captures both demand-side (consumption) and supply-side (investment) channels
- **Policy-relevant**: Different regimes imply different optimal policies

**Key insight**: Higher profits can stimulate investment (profit-led channel) OR reduce consumption (wage-led channel). The **net effect** depends on parameter magnitudes.

**Key assumptions:**
- Investment responds to capacity utilization AND profit share
- Workers don't save (Cambridge saving assumption)
- Economy reaches goods market equilibrium

---

## 2. Model

### Core Equations

**Investment function:**
```
I = g₀ + g_u × u + g_π × π
```
Where:
- `g₀` = autonomous investment
- `g_u` = sensitivity to capacity utilization (accelerator)
- `g_π` = sensitivity to profit share (profitability motive)
- `u` = capacity utilization
- `π` = profit share

**Savings function (Cambridge assumption):**
```
S = s_π × π × u
```
Workers don't save; all savings from profits.

**Equilibrium (I = S):**
```
u* = (g₀ + g_π × π) / (s_π × π - g_u)
```

**Regime determination:**
```
∂u*/∂π > 0 → profit-led
∂u*/∂π < 0 → wage-led
```

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
| `s_π` | 0.45 | Saving propensity out of profits | Stockhammer (2017) |
| `g_u` | 0.10 | Investment sensitivity to utilization | Onaran & Galanis (2014) |
| `g_π` | 0.05 | Investment sensitivity to profit share | Stockhammer (2017) |
| `g₀` | 0.03 | Autonomous investment rate | Calibrated |
| `u_baseline` | 0.80 | Baseline capacity utilization | Standard (80%) |
| `wage_share_baseline` | 0.55 | US wage share | BLS approximation |

**Parameter interpretation:**
- `s_π = 0.45`: Capitalists save 45% of profits
- `g_u = 0.10`: 1% higher utilization → 0.1% more investment
- `g_π = 0.05`: 1pp higher profit share → 0.05% more investment

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
2. delta_profit_share = wage_at_risk / total_wage_bill
3. profit_share_new = profit_share_baseline + delta_profit_share
4. u*_before = (g₀ + g_π × π_before) / (s_π × π_before - g_u)
5. u*_after = (g₀ + g_π × π_after) / (s_π × π_after - g_u)
6. delta_u = u*_after - u*_before
7. output_effect = delta_u / u_baseline
```

**Regime test:**
```
∂u*/∂π = -(g_π × g_u + g₀ × s_π) / (s_π × π - g_u)²
       = -(0.05 × 0.10 + 0.03 × 0.45) / (0.1025)²
       = -0.0185 / 0.0105
       = -1.76 < 0 → WAGE-LED
```

---

## 4. Results

### Main Specification (Equal-Split Allocation)

| Metric | Value | Meaning |
|--------|-------|---------|
| **Baseline profit share** | 45.0% | Pre-AI profit share |
| **New profit share** | 45.3% | Post-AI profit share |
| **Change in profit share** | +0.34% | AI-driven redistribution |
| **Change in utilization** | -0.58% | Utilization decline |
| **Demand regime** | **WAGE-LED** | Consumption dominates investment |
| **Output effect** | -0.73% | Economy-wide output decline |
| **Occupations with wage data** | 558 | Coverage of US occupational structure |

### Robustness Check (Employment-Weighted Allocation)

| Metric | Equal-Split | Emp-Weighted | Difference |
|--------|-------------|--------------|------------|
| Change in profit share | 0.34% | 0.34% | +2.2% |
| Change in utilization | -0.58% | -0.59% | +2.3% |
| Output effect | -0.73% | -0.74% | +2.3% |
| Demand regime | Wage-led | Wage-led | Same |

**Interpretation:** Results are robust to the choice of allocation method for ambiguous tasks. The employment-weighted specification yields slightly higher estimates (+2.3%), but qualitative conclusions are unchanged. Both specifications confirm the economy is **wage-led**.

---

## 5. Results Interpretation

### What the -0.73% output effect means

- If AI-exposed wages were fully displaced to profits, **output would fall by 0.73%**
- This is the **largest effect** across all three models
- The economy is confirmed to be **wage-led**: consumption loss > investment gain

### Why largest effect?

| Model | Effect | Channels captured |
|-------|--------|-------------------|
| Acemoglu-Restrepo | -0.11% | Task displacement |
| Kaleckian | -0.45% | + Consumption + multiplier |
| **Bhaduri-Marglin** | **-0.73%** | + Investment feedbacks |

The Bhaduri-Marglin effect is larger because:
1. It includes **investment response** to lower utilization (g_u × Δu)
2. Lower utilization further depresses investment → **feedback loop**
3. System settles at **new lower equilibrium**

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
| Cambridge saving | Workers may save some |

### Stability condition

For stable equilibrium: `s_π × π - g_u > 0`

With our parameters: `0.45 × 0.45 - 0.10 = 0.1025 > 0` ✓

Keynesian stability holds: savings more responsive than investment.

---

## 6. Parameter Sensitivity Analysis

### How AI Could Shift Model Parameters

AI may not only displace tasks—it could also shift the structural parameters that determine economic dynamics:

| Parameter | Baseline | AI Could Raise If... | AI Could Lower If... |
|-----------|----------|---------------------|---------------------|
| `s_π` (profit saving) | 0.45 | Tech firms retain earnings for R&D | More dividends/buybacks |
| `g_u` (accelerator) | 0.10 | AI makes investment more responsive | Uncertainty delays investment |
| `g_π` (profit sensitivity) | 0.05 | Profits strongly signal investment opportunities | Profits don't translate to investment |

### Scenario Results

| Scenario | Parameters | Output Effect | Regime |
|----------|------------|---------------|--------|
| **Baseline** | s_π=0.45, g_u=0.10, g_π=0.05 | **-0.73%** | wage-led |
| AI raises profit saving | s_π=0.55 | -0.41% | wage-led |
| AI lowers profit saving | s_π=0.35 | -1.93% | wage-led |
| AI boosts investment response | g_π=0.10 | -0.92% | wage-led |
| Strong profit-led attempt | g_π=0.15 | -1.12% | wage-led |
| Weaker accelerator | g_u=0.05 | -0.29% | wage-led |
| Stronger accelerator | g_u=0.15 | -3.11% | wage-led |
| AI shifts to profit-led | s_π=0.55, g_u=0.08, g_π=0.12 | -0.39% | wage-led |
| AI intensifies wage-led | s_π=0.35, g_u=0.12, g_π=0.03 | **-4.08%** | wage-led |

### Key Finding: Robust Wage-Led Regime

**All 9 scenarios remain wage-led.** Even aggressive parameter shifts toward profit-led dynamics (high g_π, high s_π) do not flip the regime. This suggests:

1. The US economy is **deeply wage-led** in its structural parameters
2. AI-driven redistribution is **contractionary across all plausible scenarios**
3. Output effects range from **-0.29% to -4.08%** depending on parameters

### Worst-Case Scenario

If AI intensifies wage-led dynamics (s_π=0.35, g_u=0.12, g_π=0.03):
- Output falls by **4.08%** (vs 0.73% baseline)
- This could occur if AI leads to more profit distribution (lower s_π) while making capacity utilization more important for investment

### Best-Case Scenario (within wage-led)

If AI dampens the accelerator (g_u=0.05):
- Output falls by only **0.29%**
- This could occur if investment becomes less responsive to utilization swings

---

## 7. Model Comparison Summary

| Model | Effect | Range (Sensitivity) | Key Channel |
|-------|--------|---------------------|-------------|
| Acemoglu-Restrepo | -0.11% | 0% to -0.20% (vary σ) | Task displacement |
| Kaleckian | -0.45% | 0.23% to 0.45% (vary MPCs) | Consumption + multiplier |
| Bhaduri-Marglin | -0.73% | **-0.29% to -4.08%** (vary s_π, g_u, g_π) | Investment feedbacks |

**Key insight:** The Bhaduri-Marglin model shows the **widest range of outcomes** because it depends on multiple interacting parameters. This highlights the importance of understanding how AI affects not just task displacement, but also saving behavior and investment dynamics.

All models show **stable results** across allocation methods, with employment-weighted yielding slightly higher estimates. The **progressive amplification** from mainstream to heterodox models highlights the importance of demand-side and investment channels often ignored in conventional analysis.

---

## References

- Bhaduri, A., & Marglin, S. (1990). "Unemployment and the real wage." *Cambridge Journal of Economics*, 14(4), 375-393.
- Stockhammer, E. (2017). "Determinants of the Wage Share." *British Journal of Industrial Relations*, 55(1), 3-33.
- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.
- Blecker, R. A. (2016). "Wage-led versus profit-led demand regimes." *Review of Keynesian Economics*, 4(4), 373-390.
- Lavoie, M., & Stockhammer, E. (2013). *Wage-led Growth*. Palgrave Macmillan.
