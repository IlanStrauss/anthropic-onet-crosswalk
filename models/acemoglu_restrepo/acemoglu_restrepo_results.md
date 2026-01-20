# Acemoglu-Restrepo Task Displacement Model

## Key Findings

| Metric | Value | Meaning |
|--------|-------|---------|
| **Wage-weighted task displacement** | 0.34% | Share of US wage bill in AI-exposed tasks |
| **Predicted wage effect (σ=1.5)** | -0.11% | Aggregate wage level decline (economy-wide average) |
| **Employment-weighted exposure** | 0.27% | Share of US employment in AI-exposed tasks |
| **Total wage bill analyzed** | $11.9 trillion | Sum of all occupation wages (TOT_EMP × A_MEAN) |

### Interpretation

Based on Anthropic API usage data linked to O*NET occupations and BLS wages:

- **0.34% of the total US wage bill** is in tasks currently being performed by Claude API
- Applying the Acemoglu-Restrepo formula with σ=1.5, this implies a **0.11% decline in the aggregate wage level** if these tasks were fully displaced
- This is an **economy-wide average effect**, not per-worker: if the model's assumptions held, average wages across all US workers would fall by 0.11%
- Workers in directly exposed occupations would experience larger effects; workers in unaffected occupations would see smaller or no effects
- The employment-weighted exposure (0.27%) is slightly lower than wage-weighted (0.34%), indicating AI tasks skew toward higher-wage occupations

### Caveats

- These estimates reflect **current API usage patterns**, not future potential
- The model assumes **full displacement** of exposed tasks (upper bound)
- **Productivity gains** and **new task creation** are not captured
- Results are sensitive to the choice of σ (elasticity parameter)

---

## Theoretical Framework

The Acemoglu-Restrepo (A-R) model is a **neoclassical task-based framework** for analyzing automation's labor market effects. It conceptualizes production as using a continuum of tasks, some performed by labor and some by capital/AI.

### Key Assumptions
- **Full employment**: Labor markets clear; displaced workers find new employment
- **Task continuum**: Production uses many tasks along a spectrum
- **Competitive markets**: Wages equal marginal product of labor

### Core Equation

The wage effect of AI-driven task displacement:

```
Δln(w) = -[(σ-1)/σ] × task_displacement_share
```

Where:
- `Δln(w)` = proportional change in wages (negative = wage decline)
- `σ` = elasticity of substitution between tasks
- `task_displacement_share` = share of wage bill in AI-exposed tasks

---

## Variables

### From Our Data

| Variable | Description | Source |
|----------|-------------|--------|
| `api_usage_count` | Number of API calls for each task | Anthropic API logs |
| `task_usage_share` | Task's share of total API usage | Calculated |
| `ai_exposure` | Occupation-level AI exposure (sum of task shares) | Aggregated |
| `wage_bill` | Total wages for occupation (`TOT_EMP × A_MEAN`) | BLS OEWS |
| `wage_share` | Occupation's share of total wage bill | Calculated |
| `emp_share` | Occupation's share of total employment | BLS OEWS |
| `TOT_EMP` | Total employment in occupation | BLS OEWS |
| `A_MEAN` | Mean annual wage | BLS OEWS |

### Parameters from Literature

| Parameter | Value | Description | Source |
|-----------|-------|-------------|--------|
| `σ` (SIGMA) | 1.5 | Elasticity of substitution between tasks | Acemoglu & Restrepo (2018, 2022) |

**Note on σ**: Values typically range from 1.0 to 2.0 in the literature:
- σ = 1: Cobb-Douglas (unit elastic)
- σ > 1: Tasks are substitutes (easier to replace workers)
- σ < 1: Tasks are complements (harder to replace)

Higher σ implies larger wage effects from displacement.

---

## Calculations

### Step 1: Calculate Wage Bill and Shares
```
wage_bill[i] = TOT_EMP[i] × A_MEAN[i]
wage_share[i] = wage_bill[i] / Σ wage_bill
emp_share[i] = TOT_EMP[i] / Σ TOT_EMP
```

### Step 2: Task Displacement Share (Wage-Weighted)
```
task_displacement_share = Σ (wage_share[i] × ai_exposure[i])
```

This weights AI exposure by each occupation's share of the total wage bill.

### Step 3: Wage Effect
```
wage_effect = -[(σ-1)/σ] × task_displacement_share
            = -[(1.5-1)/1.5] × task_displacement_share
            = -0.333 × task_displacement_share
```

---

## Results Interpretation

### Key Outputs

| Metric | Description |
|--------|-------------|
| **Wage-weighted task displacement** | Share of total wage bill exposed to AI automation |
| **Predicted wage effect** | Expected % change in wages due to displacement |
| **Employment-weighted exposure** | Alternative weighting by employment share |

### Interpreting the Wage Effect

A wage effect of **-X%** means:
- If all displaced tasks were fully automated, aggregate wages would fall by X%
- This is an **upper bound** assuming no productivity gains or new task creation
- Actual effects depend on pace of adoption and countervailing forces

### Limitations

1. **Assumes full employment**: No unemployment effects modeled
2. **No productivity gains**: Ignores potential productivity boost from AI
3. **Static analysis**: No dynamics or adjustment paths
4. **Homogeneous labor**: Doesn't capture skill heterogeneity
5. **No new task creation**: A-R theory includes task creation, but we can't measure it

---

## References

- Acemoglu, D., & Restrepo, P. (2018). "The Race between Man and Machine: Implications of Technology for Growth, Factor Shares, and Employment." *American Economic Review*, 108(6), 1488-1542.

- Acemoglu, D., & Restrepo, P. (2019). "Automation and New Tasks: How Technology Displaces and Reinstates Labor." *Journal of Economic Perspectives*, 33(2), 3-30.

- Acemoglu, D., & Restrepo, P. (2022). "Tasks, Automation, and the Rise in US Wage Inequality." *Econometrica*, 90(5), 1973-2016.
