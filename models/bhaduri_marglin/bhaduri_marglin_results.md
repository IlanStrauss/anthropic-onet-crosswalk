# Bhaduri-Marglin Endogenous Regime Model

## Theoretical Framework

The Bhaduri-Marglin (1990) model extends basic Kaleckian analysis by making **investment respond to the profit share**. This allows the model to **endogenously determine** whether an economy is wage-led or profit-led.

### Key Innovation

Unlike the basic Kaleckian model (which assumes wage-led demand), Bhaduri-Marglin recognizes that:

1. **Higher profits can stimulate investment** (profit-led channel)
2. **Higher wages stimulate consumption** (wage-led channel)
3. **Net effect depends on relative magnitudes**

The regime is determined by the parameters, not assumed a priori.

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
Workers don't save; all savings come from profits.

**Equilibrium condition:**
```
I = S
g₀ + g_u × u + g_π × π = s_π × π × u
```

**Solving for equilibrium utilization:**
```
u* = (g₀ + g_π × π) / (s_π × π - g_u)
```

**Regime determination:**
```
∂u*/∂π > 0 → profit-led demand
∂u*/∂π < 0 → wage-led demand
```

---

## Variables

### From Our Data

| Variable | Description | Source |
|----------|-------------|--------|
| `wage_at_risk` | Wage bill exposed to AI | Calculated |
| `total_wage_bill` | Sum of all occupation wage bills | BLS OEWS |
| `delta_profit_share` | Increase in profit share from AI displacement | Calculated |

### Parameters from Literature

| Parameter | Value | Description | Source |
|-----------|-------|-------------|--------|
| `s_π` | 0.45 | Propensity to save out of profits | Stockhammer (2017) |
| `g_u` | 0.10 | Investment sensitivity to utilization | Onaran & Galanis (2014) |
| `g_π` | 0.05 | Investment sensitivity to profit share | Stockhammer (2017) |
| `g₀` | 0.03 | Autonomous investment rate | Calibrated |
| `u_baseline` | 0.80 | Baseline capacity utilization | Standard |
| `wage_share_baseline` | 0.55 | US wage share (approximate) | BLS data |

**Parameter interpretation:**

- **s_π = 0.45**: Profit-earners save 45% of profit income
- **g_u = 0.10**: 1% increase in utilization → 0.1% increase in investment
- **g_π = 0.05**: 1pp increase in profit share → 0.05% increase in investment
- **g₀ = 0.03**: Base investment rate (3% of capacity)

---

## Calculations

### Step 1: Profit Share Change
```
delta_profit_share = wage_at_risk / total_wage_bill
profit_share_new = profit_share_baseline + delta_profit_share
```

AI displacing wages → transfers income from wages to profits.

### Step 2: Equilibrium Utilization Before AI
```
denominator = s_π × π_baseline - g_u
            = 0.45 × 0.45 - 0.10
            = 0.1025

u*_before = (g₀ + g_π × π_baseline) / denominator
          = (0.03 + 0.05 × 0.45) / 0.1025
          = 0.0525 / 0.1025
          ≈ 0.512
```

### Step 3: Equilibrium Utilization After AI
```
denominator_new = s_π × π_new - g_u

u*_after = (g₀ + g_π × π_new) / denominator_new
```

### Step 4: Regime Determination
```
∂u*/∂π = -(g_π × g_u + g₀ × s_π) / (s_π × π - g_u)²
```

The numerator is:
```
-(0.05 × 0.10 + 0.03 × 0.45) = -(0.005 + 0.0135) = -0.0185
```

Since numerator is **negative** and denominator is **positive** (squared):
- **∂u*/∂π < 0**
- **Regime: WAGE-LED**

### Step 5: Output Effect
```
delta_u = u*_after - u*_before
output_effect = delta_u / u_baseline
```

---

## Results Interpretation

### Key Outputs

| Metric | Description |
|--------|-------------|
| **Change in profit share** | How much wage share shifts to profits |
| **Change in capacity utilization** | Effect on output/demand |
| **Demand regime** | Wage-led or profit-led |
| **Output effect** | % change in economic activity |

### Why This Model Matters

1. **Endogenous regime**: Doesn't assume wage-led or profit-led
2. **Investment response**: Captures profit-investment link missing from basic Kaleckian
3. **Richer dynamics**: Multiple channels operating simultaneously
4. **Policy relevance**: Different regimes imply different policy responses

### Regime Implications

**If wage-led (∂u*/∂π < 0):**
- AI-driven profit share increase → **reduces** demand
- Supporting wages would boost output
- Consistent with basic Kaleckian result

**If profit-led (∂u*/∂π > 0):**
- AI-driven profit share increase → **increases** demand
- Investment response dominates consumption loss
- Would contradict basic Kaleckian

**Empirical evidence**: Most studies find US is wage-led in demand, though profit-led in growth when investment dynamics dominate.

---

## Comparison with Basic Kaleckian Model

| Feature | Basic Kaleckian | Bhaduri-Marglin |
|---------|----------------|-----------------|
| Investment | Exogenous/fixed | Responds to π and u |
| Regime | Assumed wage-led | Endogenously determined |
| Profit effect | Only consumption loss | Investment + consumption |
| Savings | From wages and profits | Only from profits |
| Complexity | Lower | Higher |

---

## Stability Condition

For a stable equilibrium, we need:
```
s_π × π - g_u > 0
```

This means saving response to utilization must exceed investment response:
- **Keynesian stability**: Savings more responsive than investment
- If violated, explosive dynamics (unstable)

With our parameters: `0.45 × 0.45 - 0.10 = 0.1025 > 0` ✓

---

## Limitations

1. **Static analysis**: No adjustment dynamics
2. **Single-sector**: Aggregated economy, no sectoral detail
3. **No financial sector**: No credit, debt, or asset prices
4. **Parameters from literature**: Not estimated from AI data specifically
5. **Linear functions**: Real investment may be non-linear in π
6. **No open economy**: Ignores trade and exchange rates

---

## References

- Bhaduri, A., & Marglin, S. (1990). "Unemployment and the real wage: The economic basis for contesting political ideologies." *Cambridge Journal of Economics*, 14(4), 375-393.

- Stockhammer, E. (2017). "Determinants of the Wage Share: A Panel Analysis of Advanced and Developing Economies." *British Journal of Industrial Relations*, 55(1), 3-33.

- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.

- Blecker, R. A. (2016). "Wage-led versus profit-led demand regimes: The long and the short of it." *Review of Keynesian Economics*, 4(4), 373-390.

- Lavoie, M., & Stockhammer, E. (2013). *Wage-led Growth: An Equitable Strategy for Economic Recovery*. Palgrave Macmillan.
