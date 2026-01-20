# Acemoglu-Restrepo Task Displacement Model

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
