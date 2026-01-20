# Kaleckian Wage Share / Aggregate Demand Model

## Key Findings

| Metric | Value |
|--------|-------|
| **Wage share reduction** | 0.34% |
| **Consumption effect** | 0.14% |
| **Keynesian multiplier** | 3.33 |
| **Aggregate demand effect** | 0.46% |
| **Employment share at risk** | 0.27% |
| **Wage bill at risk** | $41.1 billion |

### Interpretation

Applying Post-Keynesian distributional analysis to Anthropic API usage data:

- **$41.1 billion in wages** are currently in tasks performed by Claude API
- If these wages were displaced to profits, the **consumption effect would be 0.14%** (due to differential spending propensities)
- With the Keynesian multiplier (3.33), the **total aggregate demand effect is 0.46%**
- This is **larger than the Acemoglu-Restrepo wage effect (-0.11%)** because it captures demand-side feedbacks

### Why This Matters

The Kaleckian model reveals **macroeconomic risks** from AI-driven redistribution:

1. **Demand drag**: Income shifting to profits reduces consumption
2. **Multiplier amplification**: Initial shock is magnified 3.3x
3. **Unemployment risk**: 0.27% of employment in exposed occupations

### Comparison with Acemoglu-Restrepo

| Effect | A-R Model | Kaleckian |
|--------|-----------|-----------|
| Wage effect | -0.11% | — |
| AD effect | — | -0.46% |
| Mechanism | Task displacement | Consumption reduction |
| Assumes | Full employment | Demand-constrained |

The Kaleckian effect is **4x larger** because it captures the full demand chain.

---

## Theoretical Framework

The Kaleckian model is a **Post-Keynesian demand-side framework** that analyzes how income distribution affects aggregate demand. Unlike neoclassical models, it:

- **Allows unemployment**: Economy can be demand-constrained
- **Emphasizes distribution**: Wage share affects consumption and output
- **Features multiplier effects**: Initial shocks amplified through spending

### Key Insight

Workers have higher marginal propensity to consume than capitalists:
- **c_w > c_π** (workers spend more of each dollar than profit-earners)
- Therefore: **wage share ↓ → consumption ↓ → aggregate demand ↓**

This is the signature of a **wage-led demand regime**.

### Core Equations

**Consumption function:**
```
C = c_w × W + c_π × Π
```
Where W = total wages, Π = total profits

**Consumption effect of wage share change:**
```
ΔC = (c_w - c_π) × Δω
```
Where Δω = change in wage share

**With Keynesian multiplier:**
```
ΔY = κ × ΔC = [1/(1-c)] × (c_w - c_π) × Δω
```

---

## Variables

### From Our Data

| Variable | Description | Source |
|----------|-------------|--------|
| `wage_bill` | Total wages for occupation (`TOT_EMP × A_MEAN`) | BLS OEWS |
| `total_wage_bill` | Sum of all occupation wage bills | Calculated |
| `wage_at_risk` | Wage bill × AI exposure | Calculated |
| `wage_share_effect` | Wage at risk / Total wage bill | Calculated |
| `emp_at_risk` | Employment × AI exposure | Calculated |
| `TOT_EMP` | Total employment in occupation | BLS OEWS |
| `ai_exposure` | Occupation-level AI exposure | From API data |

### Parameters from Literature

| Parameter | Value | Description | Source |
|-----------|-------|-------------|--------|
| `c_w` | 0.80 | Marginal propensity to consume (wages) | Stockhammer (2011) |
| `c_π` | 0.40 | Marginal propensity to consume (profits) | Onaran & Galanis (2014) |
| `c` (AVG_C) | 0.70 | Aggregate consumption propensity | Standard Keynesian |

**Note on parameters**: These are **calibrated from existing research**, not estimated from our data. Values are typical for advanced economies:

- **c_w = 0.80**: Workers spend 80% of wage income
- **c_π = 0.40**: Profit-earners spend 40% of profit income
- **Difference = 0.40**: Each dollar shifted from wages to profits reduces consumption by $0.40

---

## Calculations

### Step 1: Wage Bill at Risk
```
wage_at_risk[i] = wage_bill[i] × ai_exposure[i]
wage_at_risk_total = Σ wage_at_risk[i]
```

### Step 2: Wage Share Effect
```
wage_share_effect = wage_at_risk_total / total_wage_bill
```

This represents the fraction of the wage bill exposed to AI displacement.

### Step 3: Consumption Effect
```
consumption_effect = (c_w - c_π) × wage_share_effect
                   = (0.80 - 0.40) × wage_share_effect
                   = 0.40 × wage_share_effect
```

### Step 4: Keynesian Multiplier
```
multiplier = 1 / (1 - AVG_C)
           = 1 / (1 - 0.70)
           = 3.33
```

### Step 5: Aggregate Demand Effect
```
ad_effect = consumption_effect × multiplier
          = 0.40 × wage_share_effect × 3.33
          = 1.33 × wage_share_effect
```

---

## Results Interpretation

### Key Outputs

| Metric | Description |
|--------|-------------|
| **Wage share reduction** | Fraction of wage bill at risk of displacement |
| **Consumption effect** | Direct reduction in consumption spending |
| **AD effect (with multiplier)** | Total demand reduction after multiplier |
| **Employment share at risk** | Fraction of employment in exposed occupations |

### Interpreting the AD Effect

An AD effect of **-X%** means:
- If all at-risk wages were displaced to profits, aggregate demand would fall by X%
- This assumes a **wage-led regime** (which the US appears to be)
- The multiplier (3.33) amplifies the initial consumption shock

### What This Model Captures That A-R Doesn't

1. **Demand-side effects**: Reduced consumption from redistribution
2. **Unemployment**: Displaced workers may not find new jobs immediately
3. **Macro feedbacks**: Lower demand → lower output → lower employment
4. **Distributional dynamics**: Who loses matters for aggregate outcomes

### Limitations

1. **Assumes wage-led regime**: May not hold in all economies/periods
2. **No investment response**: Investment held constant (addressed in Bhaduri-Marglin)
3. **Static multiplier**: Doesn't capture dynamics
4. **Linear relationships**: Real responses may be non-linear
5. **Parameters from literature**: Not estimated from our data

---

## Comparison: What Comes from Data vs. Literature

| Element | From Our Data | From Literature |
|---------|---------------|-----------------|
| AI exposure per occupation | ✓ | |
| Wage levels (A_MEAN) | ✓ | |
| Employment (TOT_EMP) | ✓ | |
| Wage bill at risk | ✓ | |
| c_w (wage MPC) | | ✓ (0.80) |
| c_π (profit MPC) | | ✓ (0.40) |
| Multiplier | | ✓ (3.33) |

---

## References

- Kalecki, M. (1971). *Selected Essays on the Dynamics of the Capitalist Economy*. Cambridge University Press.

- Stockhammer, E. (2011). "Wage-led growth: An introduction." *International Journal of Labour Research*, 3(2), 167-188.

- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.

- Lavoie, M. (2014). *Post-Keynesian Economics: New Foundations*. Edward Elgar, Chapter 6.

- Hein, E. (2014). *Distribution and Growth after Keynes*. Edward Elgar.
