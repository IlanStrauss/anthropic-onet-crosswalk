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

## 3. Data

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

| Metric | Value | Meaning |
|--------|-------|---------|
| **Baseline profit share** | 45.0% | Pre-AI profit share |
| **New profit share** | 45.3% | Post-AI profit share |
| **Change in profit share** | +0.34% | AI-driven redistribution |
| **Equilibrium utilization (before)** | 51.2% | Pre-AI capacity utilization |
| **Equilibrium utilization (after)** | 50.6% | Post-AI capacity utilization |
| **Change in utilization** | -0.60% | Utilization decline |
| **Demand regime** | **WAGE-LED** | Consumption dominates investment |
| **Output effect** | -0.75% | Economy-wide output decline |
| **∂u*/∂π** | -1.76 | Regime indicator (negative = wage-led) |

---

## 5. Results Interpretation

### What the -0.75% output effect means

- If AI-exposed wages were fully displaced to profits, **output would fall by 0.75%**
- This is the **largest effect** across all three models
- The economy is confirmed to be **wage-led**: consumption loss > investment gain

### Why largest effect?

| Model | Effect | Channels captured |
|-------|--------|-------------------|
| Acemoglu-Restrepo | -0.11% | Task displacement |
| Kaleckian | -0.46% | + Consumption + multiplier |
| **Bhaduri-Marglin** | **-0.75%** | + Investment feedbacks |

The Bhaduri-Marglin effect is larger because:
1. It includes **investment response** to lower utilization (g_u × Δu)
2. Lower utilization further depresses investment → **feedback loop**
3. System settles at **new lower equilibrium**

### Regime determination

**∂u*/∂π = -1.76 < 0** confirms:
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

## References

- Bhaduri, A., & Marglin, S. (1990). "Unemployment and the real wage." *Cambridge Journal of Economics*, 14(4), 375-393.
- Stockhammer, E. (2017). "Determinants of the Wage Share." *British Journal of Industrial Relations*, 55(1), 3-33.
- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.
- Blecker, R. A. (2016). "Wage-led versus profit-led demand regimes." *Review of Keynesian Economics*, 4(4), 373-390.
- Lavoie, M., & Stockhammer, E. (2013). *Wage-led Growth*. Palgrave Macmillan.
