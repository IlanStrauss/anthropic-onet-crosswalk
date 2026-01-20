# Theoretical Framework: AI Labor Market Effects
## Using Anthropic API Data with O*NET Crosswalk

**Author:** Ilan Strauss | AI Disclosures Project
**Date:** January 2026

---

## 1. The Problem with Anthropic's Approach

Anthropic's Economic Index is **atheoretical descriptive data**. They report:
- Task coverage rates
- Time savings estimates
- Geographic usage patterns

But they don't engage with:
- How AI enters production functions
- Labor demand elasticities
- General equilibrium effects
- Income distribution dynamics

This document outlines how to analyze AI labor market effects using **established economic theory**.

---

## 2. Mainstream Framework: Acemoglu-Restrepo Task Model

### 2.1 The Model (Acemoglu & Restrepo 2018, 2019)

Production uses a continuum of tasks indexed by `i ∈ [0, 1]`:

```
Y = ∫₀¹ y(i)^((σ-1)/σ) di)^(σ/(σ-1))
```

Each task can be produced by labor `L(i)` or capital/AI `K(i)`:

```
y(i) = γ_L(i)·L(i) + γ_K(i)·K(i)
```

**Key parameters:**
- `σ` = elasticity of substitution between tasks
- `γ_L(i)` = labor productivity in task i
- `γ_K(i)` = AI/capital productivity in task i
- `I` = threshold task (tasks below I automated)

### 2.2 Automation Effect

When AI automates tasks [I_old, I_new]:

```
d ln(w/r) = -[(σ-1)/σ] × [task displacement share] + [productivity effect]
```

**Wage effect depends on:**
1. **Displacement effect** (negative): AI replaces labor in tasks
2. **Productivity effect** (positive): higher output raises labor demand
3. **New task creation** (positive): new tasks where labor has advantage

### 2.3 Operationalizing with Our Data

| A-R Concept | Our Data Variable | Measurement |
|-------------|-------------------|-------------|
| Task `i` | `onet_task_id` | Individual O*NET tasks |
| Automation threshold `I` | `api_usage_count > 0` | Tasks with Claude usage |
| Labor productivity `γ_L` | `human_only_time` | Anthropic's time estimate |
| AI productivity `γ_K` | `human_with_ai_time` | Anthropic's time estimate |
| Task importance | O*NET `Task Ratings` | Importance × Frequency |

**Estimation approach:**

1. **Calculate task displacement share:**
   ```
   Displacement = Σ (wage_share × automation_probability)
   ```
   Where automation_probability = f(api_usage_count, task_success_rate)

2. **Estimate wage effects by occupation:**
   ```
   Δ ln(wage_j) = β₁·(task_displacement_j) + β₂·(productivity_gain_j) + ε
   ```

3. **Required additional data:**
   - BLS wages by SOC code
   - Employment levels by occupation
   - Task importance weights from O*NET

---

## 3. Heterodox Framework I: Aggregate Demand Effects

### 3.1 Post-Keynesian Model

AI affects aggregate demand through multiple channels:

```
AD = C + I + G + (X - M)
```

**Channel 1: Wage share and consumption**
```
C = c_w·W + c_π·Π
```
Where `c_w > c_π` (workers have higher MPC)

If AI reduces wage share: `W/Y ↓` → `C ↓` → `AD ↓`

**Channel 2: Investment**
```
I = I(r, u, g^e)
```
- `r` = profit rate
- `u` = capacity utilization
- `g^e` = expected growth

AI may raise profits but reduce utilization if demand falls.

**Channel 3: Income distribution**
```
ω = W/Y = (w·L)/(P·Y) = (w/p)/(Y/L)
```

AI raises `Y/L` (productivity) but may reduce `L` or `w`.

### 3.2 Operationalizing with Our Data

| Concept | Measurement | Data Source |
|---------|-------------|-------------|
| Wage share impact | Σ(occupation_wage × displacement) | BLS + our crosswalk |
| Productivity gain | Σ(time_savings × task_importance) | Anthropic + O*NET |
| Employment at risk | Σ(employment × automation_prob) | BLS + our crosswalk |
| Sectoral distribution | Industry breakdown of affected tasks | O*NET + BLS |

**Key question:** Does AI lead to **wage-led** or **profit-led** growth regime?

- **Wage-led:** Wage cuts reduce demand more than they stimulate investment
- **Profit-led:** Wage cuts boost investment enough to offset demand loss

**Estimation:**
```
g = α₀ + α₁·ω + α₂·(AI_exposure) + ε
```
Test whether `α₁ > 0` (wage-led) and sign of `α₂`.

---

## 4. Heterodox Framework II: Profitability Analysis

### 4.1 Marxist Rate of Profit

```
r = s / (c + v) = (s/v) / (c/v + 1) = e / (OCC + 1)
```

Where:
- `s` = surplus value
- `v` = variable capital (wages)
- `c` = constant capital (machines, AI)
- `e = s/v` = rate of exploitation
- `OCC = c/v` = organic composition of capital

**AI's contradictory effects:**

1. **Raises exploitation `e`:** More output per worker-hour
2. **Raises OCC:** AI requires capital investment
3. **Net effect on `r` ambiguous**

### 4.2 Operationalizing with Our Data

| Concept | Proxy | Data |
|---------|-------|------|
| Labor displaced | Task automation × employment | Our crosswalk + BLS |
| Value added per worker | Productivity × wage | BLS |
| Capital requirements | AI infrastructure costs | Industry estimates |
| Exploitation rate change | (productivity_gain - wage_gain) / wage | BLS time series |

**Estimation:**
```
Δr = f(Δe, ΔOCC) = f(AI_productivity_effect, AI_capital_intensity)
```

---

## 5. Comparative Framework: Skill-Biased vs Task-Based

### 5.1 Traditional SBTC (Bound & Johnson 1992, Katz & Murphy 1992)

```
ln(w_H/w_L) = (1/σ)·[D_H - D_L] + [(σ-1)/σ]·θ_t
```

AI is skill-biased if it raises relative demand for skilled labor.

### 5.2 Task-Based Alternative (Autor, Levy, Murnane 2003)

Classify tasks as:
- **Routine cognitive** (bookkeeping, data entry)
- **Routine manual** (assembly, repetitive physical)
- **Non-routine cognitive** (analysis, management)
- **Non-routine manual** (care work, craft)

AI automates **routine** tasks (cognitive > manual).

### 5.3 Testing with Our Data

**Step 1:** Classify O*NET tasks into routine/non-routine
- Use existing crosswalks (Autor & Dorn 2013)
- Or machine learning classification

**Step 2:** Calculate routine task intensity by occupation:
```
RTI_j = ln(Routine_j / Non-routine_j)
```

**Step 3:** Test if Claude usage correlates with RTI:
```
API_usage_j = β₀ + β₁·RTI_j + β₂·education_j + ε
```

**Hypothesis:** If Claude follows RBTC pattern, `β₁ > 0`

---

## 6. Data Requirements Summary

| Variable | Source | Status |
|----------|--------|--------|
| API task usage | Anthropic | ✓ Have |
| O*NET task IDs | Our crosswalk | ✓ Have |
| SOC codes | Our crosswalk | ✓ Have |
| Job Zone | O*NET | ✓ Have |
| Task importance | O*NET Task Ratings | Need to add |
| Routine/non-routine | Autor-Dorn crosswalk | Need to add |
| BLS wages | OEWS | Need to add |
| BLS employment | OEWS | Need to add |
| Industry breakdown | BLS | Need to add |

---

## 7. Research Questions

### Mainstream Questions:
1. What is the **task displacement share** from Claude adoption?
2. Does displacement exceed productivity gains (net job loss)?
3. Which occupations face highest **automation risk**?
4. Is there evidence of **new task creation**?

### Heterodox Questions:
1. Does AI adoption **reduce the wage share**?
2. Is the economy **wage-led or profit-led** in response to AI?
3. Does AI raise or lower the **rate of profit**?
4. What are the **aggregate demand** effects of AI-driven displacement?
5. Does AI increase **income inequality** within and between countries?

### Methodological Questions:
1. Is Claude usage a good **proxy for AI automation** broadly?
2. How does **API usage differ from consumer usage** (Claude.ai)?
3. What is the **selection bias** in Anthropic's data?

---

## 8. Limitations of Anthropic's Data

1. **Single product:** Claude only, not AI broadly
2. **Selection bias:** Users who choose Claude, not random sample
3. **No prices:** Can't estimate demand elasticities
4. **No longitudinal:** Cross-section, can't identify causal effects
5. **No firm data:** Can't link to productivity/profit outcomes
6. **Interpretation:** "Task usage" ≠ "task automation"

---

## 9. Next Steps

1. **Add O*NET task ratings** (importance, frequency, level)
2. **Add routine/non-routine classification**
3. **Link to BLS wages and employment**
4. **Estimate task displacement share**
5. **Calculate wage-weighted AI exposure by occupation**
6. **Compare to existing AI exposure indices**
7. **Build aggregate demand simulation model**

---

## References

- Acemoglu, D. & Autor, D. (2011). Skills, tasks and technologies. *Handbook of Labor Economics*.
- Acemoglu, D. & Restrepo, P. (2018). The race between man and machine. *American Economic Review*.
- Acemoglu, D. & Restrepo, P. (2019). Automation and new tasks. *Journal of Economic Perspectives*.
- Autor, D., Levy, F. & Murnane, R. (2003). The skill content of recent technological change. *QJE*.
- Autor, D. & Dorn, D. (2013). The growth of low-skill service jobs. *American Economic Review*.
- Eloundou, T. et al. (2023). GPTs are GPTs. *arXiv*.
- Felten, E. et al. (2021). Occupational, industry, and geographic exposure to AI. *Working paper*.
- Webb, M. (2020). The impact of AI on the labor market. *Stanford working paper*.

---

*Document prepared for AI Disclosures Project*
