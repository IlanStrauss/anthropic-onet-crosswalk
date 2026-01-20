# Kaleckian Wage Share / Aggregate Demand Model

## 1. Introduction & Motivation

The Kaleckian model is a **Post-Keynesian demand-side framework** that captures macroeconomic effects missing from mainstream models.

**Why use this model?**

- **Demand matters**: Mainstream models assume full employment; Kaleckian allows demand-constrained output
- **Distribution affects growth**: Income distribution is not neutral—it affects aggregate demand
- **Unemployment possible**: Workers displaced by AI may not find new jobs immediately
- **Multiplier effects**: Initial shocks are amplified through spending chains

**Key insight**: Workers spend more of their income than capitalists (c_w > c_π), so shifting income from wages to profits **reduces** aggregate consumption and demand.

**Key assumptions:**
- Demand-constrained economy (not full employment)
- Differential propensities to consume by income class
- Investment held constant (relaxed in Bhaduri-Marglin)

---

## 2. Model

### Core Equations

**Consumption function:**
```
C = c_w × W + c_π × Π
```
Where: W = wages, Π = profits, c_w = wage MPC, c_π = profit MPC

**Consumption effect of wage share change:**
```
ΔC = (c_w - c_π) × Δω
```
Where: Δω = change in wage share

**With Keynesian multiplier:**
```
ΔY = κ × ΔC = [1/(1-c)] × (c_w - c_π) × Δω
```

### Mechanism

1. AI displaces labor tasks → wages fall, profits rise
2. Income shifts from high-spending workers to low-spending capitalists
3. Consumption falls: ΔC = (0.80 - 0.40) × Δω
4. Multiplier amplifies: ΔY = 3.33 × ΔC
5. Aggregate demand contracts

---

## 3. Data

### Variables from Our Data

| Variable | Description | Source |
|----------|-------------|--------|
| `api_usage_count` | API calls per task | Anthropic API logs |
| `ai_exposure` | Occupation-level AI exposure | Calculated from API data |
| `TOT_EMP` | Employment per occupation | BLS OEWS |
| `A_MEAN` | Mean annual wage | BLS OEWS |
| `wage_bill` | `TOT_EMP × A_MEAN` | Calculated |
| `wage_at_risk` | `wage_bill × ai_exposure` | Calculated |
| `emp_at_risk` | `TOT_EMP × ai_exposure` | Calculated |

### Parameters from Literature

| Parameter | Value | Description | Source |
|-----------|-------|-------------|--------|
| `c_w` | 0.80 | Marginal propensity to consume (wages) | Stockhammer (2011) |
| `c_π` | 0.40 | Marginal propensity to consume (profits) | Onaran & Galanis (2014) |
| `c` | 0.70 | Aggregate consumption propensity | Standard Keynesian |

**Parameter interpretation:**
- Workers spend 80 cents of each dollar earned
- Profit-earners spend 40 cents of each dollar
- Difference (40 cents) = consumption loss per dollar shifted from wages to profits

### Calculation Steps

```
1. wage_at_risk = Σ (wage_bill[i] × ai_exposure[i])
2. wage_share_effect = wage_at_risk / total_wage_bill
3. consumption_effect = (c_w - c_π) × wage_share_effect = 0.40 × wage_share_effect
4. multiplier = 1 / (1 - c) = 1 / 0.30 = 3.33
5. ad_effect = consumption_effect × multiplier
```

---

## 4. Results

| Metric | Value | Meaning |
|--------|-------|---------|
| **Wage share reduction** | 0.34% | Fraction of wage bill at risk |
| **Consumption effect** | 0.14% | Direct reduction in consumption |
| **Keynesian multiplier** | 3.33 | Amplification factor |
| **AD effect (with multiplier)** | 0.46% | Total demand reduction |
| **Employment share at risk** | 0.27% | Share of jobs in exposed occupations |
| **Wage bill at risk** | $41.1 billion | Dollar value of exposed wages |

---

## 5. Results Interpretation

### What the -0.46% AD effect means

- If AI-exposed wages were fully displaced to profits, **aggregate demand would fall by 0.46%**
- This is **4x larger** than the Acemoglu-Restrepo wage effect (-0.11%)
- The difference comes from:
  1. **Consumption channel**: Income redistribution reduces spending
  2. **Multiplier amplification**: 3.33x magnification of initial shock

### Why larger than Acemoglu-Restrepo?

| Model | Captures | Effect |
|-------|----------|--------|
| A-R | Supply-side task displacement | -0.11% |
| Kaleckian | + Consumption reduction | -0.46% |
| | + Multiplier effects | |

The Kaleckian model reveals **demand-side risks** invisible to supply-side models.

### Policy implications

- In a **wage-led demand regime**, AI-driven redistribution is contractionary
- Policies supporting wages (minimum wage, unions, profit-sharing) would offset demand drag
- Fiscal policy may be needed to stabilize demand

### Caveats

| Caveat | Implication |
|--------|-------------|
| Assumes wage-led regime | May not hold everywhere |
| Investment held constant | Addressed in Bhaduri-Marglin |
| Parameters from literature | Not estimated from AI data |
| Static analysis | No dynamics modeled |

### Comparison across models

| Model | Effect | What it captures |
|-------|--------|------------------|
| Acemoglu-Restrepo | -0.11% | Task displacement only |
| **Kaleckian** | **-0.46%** | + Consumption + multiplier |
| Bhaduri-Marglin | -0.75% | + Investment feedbacks |

---

## References

- Kalecki, M. (1971). *Selected Essays on the Dynamics of the Capitalist Economy*. Cambridge.
- Stockhammer, E. (2011). "Wage-led growth: An introduction." *International Journal of Labour Research*, 3(2), 167-188.
- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.
- Lavoie, M. (2014). *Post-Keynesian Economics: New Foundations*. Edward Elgar.
- Hein, E. (2014). *Distribution and Growth after Keynes*. Edward Elgar.
