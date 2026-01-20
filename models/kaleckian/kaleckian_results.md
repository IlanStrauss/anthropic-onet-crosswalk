# Kaleckian Wage Share / Aggregate Demand Model

## 1. Introduction & Motivation

The Kaleckian model is a **Post-Keynesian demand-side framework** that captures macroeconomic effects missing from mainstream models.

**Why use this model?**

- **Demand matters**: Mainstream models assume full employment; Kaleckian allows demand-constrained output
- **Distribution affects growth**: Income distribution is not neutral—it affects aggregate demand
- **Unemployment possible**: Workers displaced by AI may not find new jobs immediately
- **Multiplier effects**: Initial shocks are amplified through spending chains

**Key insight**: Workers spend more of their income than capitalists (c_w > c_π), so shifting income from wages to profits **reduces** aggregate consumption and demand.

**Important framing:**

This is a **demand-side stress test**, not a regime identification exercise. With c_w > c_π assumed and investment held constant, wage-led demand is built into the model structure.

**Key assumptions:**
- Demand-constrained economy (not full employment)
- Differential propensities to consume by income class
- Investment held constant (relaxed in Bhaduri-Marglin)
- Closed economy: Y = C(Y,ω) + I + G (I, G exogenous)

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
ΔC/Y = (c_w - c_π) × Δω
```
Where: Δω = change in wage share (negative if wages fall)

**CORRECTED: Change in wage share of income:**
```
Δω = -ω₀ × (wage_at_risk / total_wages)
```
Note: This converts from "fraction of wages displaced" to "change in wage share of total income"

**CORRECTED: Multiplier derived from class MPCs:**
```
c = c_w × ω + c_π × (1-ω)    (aggregate MPC)
κ = 1 / (1 - c)               (derived multiplier)
```
With ω₀=0.55, c_w=0.80, c_π=0.40: c=0.62, κ≈2.63

**AD effect:**
```
ΔY/Y = κ × (c_w - c_π) × Δω   (negative = contractionary)
```

### Mechanism

1. AI displaces labor tasks → wages fall, profits rise
2. Income shifts from high-spending workers to low-spending capitalists
3. Wage share falls: Δω = -0.55 × 0.34% = -0.19%
4. Consumption falls: ΔC/Y = (0.40) × (-0.19%) = -0.07%
5. Multiplier amplifies: ΔY/Y = 2.63 × (-0.07%) = -0.19%
6. Aggregate demand contracts

---

## 3. Data & Methodology

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
| `ω₀` | 0.55 | Baseline wage share of income | BLS approximation |
| `c` | 0.62 | **Derived** aggregate MPC: c_w×ω + c_π×(1-ω) | Calculated |
| `κ` | 2.63 | **Derived** multiplier: 1/(1-c) | Calculated |

**Parameter interpretation:**
- Workers spend 80 cents of each dollar earned
- Profit-earners spend 40 cents of each dollar
- Difference (40 cents) = consumption loss per dollar shifted from wages to profits
- Aggregate MPC derived from distribution: 0.80×0.55 + 0.40×0.45 = 0.62

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
1. wage_at_risk = Σ (wage_bill[i] × ai_exposure[i])
2. wage_fraction_at_risk = wage_at_risk / total_wage_bill = 0.34%
3. delta_omega = -ω₀ × wage_fraction_at_risk = -0.55 × 0.34% = -0.19%
   (CORRECTED: Convert wage fraction to change in wage SHARE of income)
4. aggregate_mpc = c_w × ω₀ + c_π × (1-ω₀) = 0.62
5. multiplier = 1 / (1 - aggregate_mpc) = 2.63
   (CORRECTED: Derived from class MPCs, not exogenous)
6. consumption_effect = (c_w - c_π) × delta_omega = -0.07%
7. ad_effect = consumption_effect × multiplier = -0.19%
   (Negative = contractionary)
```

---

## 4. Results

### Main Specification (Equal-Split Allocation)

| Metric | Value | Meaning |
|--------|-------|---------|
| **Wage fraction at risk** | 0.34% | Fraction of wage bill in exposed tasks |
| **Change in wage share (Δω)** | -0.19% | Actual change in wage share of income |
| **Derived multiplier** | 2.04 | From c = c_w×ω + c_π×(1-ω) |
| **AD effect (ΔY/Y)** | **-0.19%** | Contractionary (negative sign) |
| **Employment share at risk** | 0.26% | Share of jobs in exposed occupations |
| **Occupations with wage data** | 558 | Coverage of US occupational structure |

### Robustness Check (Employment-Weighted Allocation)

| Metric | Equal-Split | Emp-Weighted | Difference |
|--------|-------------|--------------|------------|
| Wage fraction at risk | 0.34% | 0.34% | +2.2% |
| AD effect | -0.19% | -0.20% | +2.2% |
| Employment at risk | 0.26% | 0.27% | +2.0% |

**Interpretation:** Results are robust to the choice of allocation method for ambiguous tasks. The employment-weighted specification yields slightly higher estimates (+2.2%), but qualitative conclusions are unchanged.

---

## 5. Results Interpretation

### What the -0.19% AD effect means

- If AI-exposed wages were fully displaced to profits, **aggregate demand would fall by 0.19%**
- This is **1.7x larger** than the Acemoglu-Restrepo wage effect (-0.11%)
- The difference comes from:
  1. **Consumption channel**: Income redistribution reduces spending
  2. **Multiplier amplification**: 2.04x magnification of initial shock

### Why larger than Acemoglu-Restrepo?

| Model | Captures | Effect |
|-------|----------|--------|
| A-R | Supply-side task displacement | -0.11% |
| Kaleckian | + Consumption channel | -0.19% |
| | + Derived multiplier (2.04x) | |

The Kaleckian model captures **demand-side effects** beyond supply-side task reallocation.

### Policy implications

Under the assumed Post-Keynesian structure (c_w > c_π, investment constant), AI-driven redistribution toward profits is contractionary. Policies supporting wages could offset demand effects.

### Caveats

| Caveat | Implication |
|--------|-------------|
| Wage-led is assumed (c_w > c_π) | Not a discovered regime |
| Investment held constant | Addressed in Bhaduri-Marglin |
| Parameters from literature | Not estimated from AI data |
| Static analysis | No dynamics modeled |
| 100% displacement assumed | Actual rate (α) is unknown |

### Comparison across models

| Model | Effect | What it captures |
|-------|--------|------------------|
| Acemoglu-Restrepo | -0.11% | Supply-side displacement (pessimistic) |
| **Kaleckian** | **-0.19%** | + Consumption + derived multiplier |
| Bhaduri-Marglin | -0.39% | + Investment feedbacks |

---

## 6. Parameter Sensitivity: Marginal Propensities to Consume

The AD effect depends on the difference between worker and capitalist consumption propensities. AI could shift these if it changes income composition or spending behavior.

### Scenario Results

| Scenario | c_w | c_π | AD Effect | Derived κ |
|----------|-----|-----|-----------|-----------|
| **Baseline** | 0.80 | 0.40 | **-0.19%** | 2.04 |
| AI concentrates profits in low-spending tech firms | 0.80 | 0.30 | -0.25% | 2.12 |
| Workers save more (precarity, gig economy) | 0.70 | 0.40 | -0.13% | 1.85 |
| Financialization: more shareholder payouts | 0.75 | 0.50 | -0.13% | 1.79 |
| Stronger wage-led: workers spend more | 0.85 | 0.35 | -0.25% | 2.22 |

### Interpretation

- **All scenarios remain contractionary** because c_w > c_π in all cases
- The AD effect ranges from **-0.13% to -0.25%** depending on consumption propensities
- If AI concentrates profits in low-spending tech firms (c_π falls), the AD effect **increases**
- If workers become more precarious and save more (c_w falls), the AD effect **decreases**

### Key Insight

The contractionary result is built into the model: with c_w > c_π and investment held constant, any redistribution toward profits reduces consumption and aggregate demand. This is not a discovered regime—it's a maintained assumption.

### What Would Flip the Result?

For expansionary effects, we would need either:
1. c_π > c_w (implausible), OR
2. Endogenous investment that responds to profits (addressed in Bhaduri-Marglin)

---

## References

- Kalecki, M. (1971). *Selected Essays on the Dynamics of the Capitalist Economy*. Cambridge.
- Stockhammer, E. (2011). "Wage-led growth: An introduction." *International Journal of Labour Research*, 3(2), 167-188.
- Onaran, O., & Galanis, G. (2014). "Income distribution and growth: A global model." *Environment and Planning A*, 46(10), 2489-2513.
- Lavoie, M. (2014). *Post-Keynesian Economics: New Foundations*. Edward Elgar.
- Hein, E. (2014). *Distribution and Growth after Keynes*. Edward Elgar.
