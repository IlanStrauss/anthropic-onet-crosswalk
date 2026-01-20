# Acemoglu-Restrepo Inspired Task Model

## 1. Introduction & Motivation

This model is a **didactic reduced-form proxy** inspired by the Acemoglu-Restrepo (A-R) task-based framework, widely cited in automation literature.

**Important caveats:**

- This is NOT the exact A-R framework—it's a simplified benchmark
- Claude API usage measures **where Claude is used**, not tasks actually displaced to capital
- Usage may reflect **complementarity** (productivity gains) as much as **substitution**
- True A-R has both: **Net Effect = Productivity Effect − Displacement Effect**
- We report φ=0 (no productivity gains) as a **pessimistic upper bound** on displacement

**Why use this model?**

- **Mainstream benchmark**: A-R is a widely cited task-based framework in automation literature
- **Comparability**: Enables comparison with existing automation studies
- **Clean baseline**: Full employment provides a stylized benchmark (not necessarily a lower bound)

**Key assumptions:**
- Full employment (labor markets clear)
- Competitive markets (wages = marginal product)
- Production uses a continuum of tasks
- **100% displacement assumed** (α=1): All exposed tasks are displaced (pessimistic)

---

## 2. Model

### Core Equation

Our proxy equation for the wage effect:

```
Δln(w) = φ × exposure_share - [(σ-1)/σ] × α × exposure_share
       = (φ - [(σ-1)/σ] × α) × exposure_share
```

Where:
- `Δln(w)` = proportional change in aggregate wage level
- `φ` = productivity effect (set to 0, pessimistic case)
- `σ` = elasticity of substitution between tasks
- `α` = displacement rate (fraction of exposed tasks actually displaced)
- `exposure_share` = wage-weighted AI usage exposure (NOT displacement)

**Note:** This is a simplified proxy, not the exact A-R formulation. True A-R derives these terms from equilibrium conditions in a CES task aggregator.

### Mechanism

1. Production requires many tasks along a continuum
2. AI is used in some tasks (but may complement or substitute labor)
3. If substitution: labor demand for those tasks falls
4. Aggregate wage level adjusts downward
5. Workers reallocate to remaining tasks (full employment maintained)

### Parameters

| Parameter | Value | Description | Source |
|-----------|-------|-------------|--------|
| `σ` (SIGMA) | 1.5 | Elasticity of substitution | A-R (2018) baseline |
| `α` (ALPHA) | 1.0 | Displacement rate (pessimistic) | Assumed |
| `φ` (PHI) | 0.0 | Productivity effect (pessimistic) | Assumed |

**Note on σ**: Higher σ means tasks are **more substitutable** (easier to replace labor with capital).
- At σ=1 (Cobb-Douglas): displacement term vanishes—workers simply reallocate
- As σ→∞: wage effect approaches -α × exposure_share
- Literature range: 1.0–2.0

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
3. exposure_share = Σ (wage_share[i] × ai_exposure[i])
4. displacement_effect = -[(σ-1)/σ] × α × exposure_share
5. productivity_effect = φ × exposure_share  (= 0 with φ=0)
6. wage_effect = productivity_effect + displacement_effect
```

---

## 4. Results

### Main Specification (Equal-Split Allocation)

| Metric | Value | Meaning |
|--------|-------|---------|
| **Wage-weighted exposure share** | 0.34% | Share of US wage bill where Claude is used |
| **Predicted wage effect (σ=1.5, α=1, φ=0)** | -0.11% | Pessimistic: full displacement, no productivity gains |
| **Employment-weighted exposure** | 0.26% | Share of US employment where Claude is used |
| **Occupations with wage data** | 558 | Coverage of US occupational structure |

### Robustness Check (Employment-Weighted Allocation)

| Metric | Equal-Split | Emp-Weighted | Difference |
|--------|-------------|--------------|------------|
| Exposure share | 0.34% | 0.34% | +2.2% |
| Wage effect | -0.11% | -0.11% | +2.2% |

**Interpretation:** Results are robust to the choice of allocation method for ambiguous tasks. The employment-weighted specification yields slightly higher estimates (+2.2%), but qualitative conclusions are unchanged.

---

## 5. Results Interpretation

### What the -0.11% means

- The **aggregate US wage level** would decline by 0.11% under pessimistic assumptions (α=1, φ=0)
- This is an **economy-wide average**, not per-worker
- Workers in exposed occupations would experience **larger** effects
- Workers in unaffected occupations would see **smaller or no** effects

### Critical limitation

**Claude API usage is not direct evidence of automation.** It may represent complementarity/productivity improvements, so we interpret results as an illustrative upper bound under full displacement of exposed tasks.

### Context

- **0.34% of the US wage bill** is in tasks where Claude is currently used
- This is a **modest effect** reflecting early-stage LLM adoption
- Employment-weighted exposure (0.26%) < wage-weighted (0.34%) → AI tasks skew toward **higher-wage occupations**

### Caveats

| Caveat | Implication |
|--------|-------------|
| Usage ≠ displacement | Effect may be zero or positive (complementarity) |
| Assumes full displacement (α=1) | Upper bound estimate |
| No productivity gains (φ=0) | Effect may be offset |
| No new task creation | A-R theory includes this, but we can't measure it |
| Current usage only | Future exposure likely higher |
| Full employment assumed | No unemployment modeled |

### Comparison with heterodox models

| Model | Effect | Key difference |
|-------|--------|----------------|
| **This model** | -0.11% | Supply-side only, full displacement assumed |
| Kaleckian | -0.19% | + Demand effects (consumption channel) |
| Bhaduri-Marglin | -0.39% | + Investment feedbacks |

---

## 6. Parameter Sensitivity: Elasticity of Substitution (σ)

The wage effect depends on σ, the elasticity of substitution between tasks. We use σ as a **reduced-form sensitivity knob**, not its full structural interpretation.

### Scenario Results

**What this table shows:** How Δln(w) (change in economy-wide average wage level) varies with σ (elasticity of substitution between tasks).

| σ (elasticity) | Description | Δln(w) (aggregate wage change) |
|----------------|-------------|--------------------------------|
| 1.0 | Cobb-Douglas (displacement term vanishes) | **0.00%** |
| 1.25 | Lower substitutability | -0.07% |
| **1.5** | **Baseline** | **-0.11%** |
| 2.0 | Higher substitutability | -0.17% |
| 2.5 | Very high | **-0.20%** |

### Interpretation

- At σ=1 (Cobb-Douglas), the displacement term vanishes—workers reallocate without wage loss
- Higher σ means tasks are **more substitutable** (labor more easily replaced by capital)
- As σ→∞, wage effect approaches the full exposure share

**Note:** In CES task aggregators, σ's exact role is more nuanced. We use it here as a sensitivity parameter to show the range of possible effects.

### Literature Range

Published estimates of σ vary:
- Acemoglu & Restrepo (2018): σ ≈ 1.5
- Earlier automation literature: σ ≈ 0.6–2.0
- A-R sensitivity analyses sometimes use 0.6–1.2 as well

---

## References

- Acemoglu, D., & Restrepo, P. (2018). "The Race between Man and Machine." *American Economic Review*, 108(6), 1488-1542.
- Acemoglu, D., & Restrepo, P. (2019). "Automation and New Tasks." *Journal of Economic Perspectives*, 33(2), 3-30.
- Acemoglu, D., & Restrepo, P. (2022). "Tasks, Automation, and the Rise in US Wage Inequality." *Econometrica*, 90(5), 1973-2016.
