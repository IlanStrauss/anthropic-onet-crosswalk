# Acemoglu-Restrepo Task Displacement Model

## 1. Introduction & Motivation

The Acemoglu-Restrepo (A-R) model is the **dominant mainstream framework** for analyzing automation's labor market effects. It provides a rigorous, microfounded approach grounded in neoclassical economics.

**Why use this model?**

- **Theoretical rigor**: Derived from first principles with clear assumptions
- **Policy relevance**: Widely cited in policy discussions (IMF, OECD, World Bank)
- **Comparability**: Enables comparison with existing automation literature
- **Conservative baseline**: Full employment assumption provides lower-bound estimates

**Key assumptions:**
- Full employment (labor markets clear)
- Competitive markets (wages = marginal product)
- Production uses a continuum of tasks

---

## 2. Model

### Core Equation

The wage effect of AI-driven task displacement:

```
Δln(w) = -[(σ-1)/σ] × task_displacement_share
```

Where:
- `Δln(w)` = proportional change in aggregate wage level
- `σ` = elasticity of substitution between tasks
- `task_displacement_share` = share of wage bill in AI-exposed tasks

### Mechanism

1. Production requires many tasks along a continuum
2. AI automates some tasks previously done by labor
3. Labor demand for those tasks falls
4. Aggregate wage level adjusts downward
5. Workers reallocate to remaining tasks (full employment maintained)

### Parameter

| Parameter | Value | Source |
|-----------|-------|--------|
| `σ` (SIGMA) | 1.5 | Acemoglu & Restrepo (2018, 2022) |

**Note on σ**: Higher values imply larger wage effects. Literature range: 1.0–2.0.

---

## 3. Data & Methodology

### From Anthropic API / O*NET / BLS

| Variable | Description | Source |
|----------|-------------|--------|
| `api_usage_count` | API calls per task | Anthropic API logs |
| `task_usage_share` | Task's share of total API usage | Calculated |
| `ai_exposure` | Occupation-level exposure (sum of task shares) | Aggregated |
| `TOT_EMP` | Total employment per occupation | BLS OEWS |
| `A_MEAN` | Mean annual wage per occupation | BLS OEWS |
| `wage_bill` | `TOT_EMP × A_MEAN` | Calculated |
| `wage_share` | Occupation's share of total wage bill | Calculated |

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
1. wage_bill[i] = TOT_EMP[i] × A_MEAN[i]
2. wage_share[i] = wage_bill[i] / Σ wage_bill
3. task_displacement_share = Σ (wage_share[i] × ai_exposure[i])
4. wage_effect = -[(σ-1)/σ] × task_displacement_share
```

---

## 4. Results

### Main Specification (Equal-Split Allocation)

| Metric | Value | Meaning |
|--------|-------|---------|
| **Wage-weighted task displacement** | 0.34% | Share of US wage bill in AI-exposed tasks |
| **Predicted wage effect (σ=1.5)** | -0.11% | Aggregate wage level decline (economy-wide average) |
| **Employment-weighted exposure** | 0.26% | Share of US employment in AI-exposed tasks |
| **Occupations with wage data** | 558 | Coverage of US occupational structure |

### Robustness Check (Employment-Weighted Allocation)

| Metric | Equal-Split | Emp-Weighted | Difference |
|--------|-------------|--------------|------------|
| Task displacement | 0.34% | 0.34% | +2.2% |
| Wage effect | -0.11% | -0.11% | +2.2% |

**Interpretation:** Results are robust to the choice of allocation method for ambiguous tasks. The employment-weighted specification yields slightly higher estimates (+2.2%), but qualitative conclusions are unchanged.

---

## 5. Results Interpretation

### What the -0.11% means

- The **aggregate US wage level** would decline by 0.11% if all exposed tasks were fully automated
- This is an **economy-wide average**, not per-worker
- Workers in exposed occupations would experience **larger** effects
- Workers in unaffected occupations would see **smaller or no** effects

### Context

- **0.34% of the US wage bill** is currently in tasks performed by Claude API
- This is a **modest effect** reflecting early-stage LLM adoption
- Employment-weighted exposure (0.26%) < wage-weighted (0.34%) → AI tasks skew toward **higher-wage occupations**

### Caveats

| Caveat | Implication |
|--------|-------------|
| Assumes full displacement | Upper bound estimate |
| No productivity gains captured | Effect may be offset |
| No new task creation | A-R theory includes this, but we can't measure it |
| Current usage only | Future exposure likely higher |
| Full employment assumed | No unemployment modeled |

### Comparison with heterodox models

| Model | Effect | Why different |
|-------|--------|---------------|
| **Acemoglu-Restrepo** | -0.11% | Supply-side only |
| Kaleckian | -0.45% | Adds demand effects |
| Bhaduri-Marglin | -0.73% | Adds investment feedbacks |

---

## References

- Acemoglu, D., & Restrepo, P. (2018). "The Race between Man and Machine." *American Economic Review*, 108(6), 1488-1542.
- Acemoglu, D., & Restrepo, P. (2019). "Automation and New Tasks." *Journal of Economic Perspectives*, 33(2), 3-30.
- Acemoglu, D., & Restrepo, P. (2022). "Tasks, Automation, and the Rise in US Wage Inequality." *Econometrica*, 90(5), 1973-2016.
