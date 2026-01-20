# =============================================================================
# Estimate AI Labor Market Effects: Mainstream & Heterodox Models
# =============================================================================
#
# Two theoretical frameworks applied to Anthropic API task exposure data:
#
# 1. ACEMOGLU-RESTREPO: Task displacement model (neoclassical)
#    - Assumes full employment, calculates wage effects from task reallocation
#    - Key equation: Δln(w) = -[(σ-1)/σ] × displacement_share
#
# 2. KALECKIAN: Wage share / aggregate demand model (Post-Keynesian)
#    - Allows unemployment, demand-constrained output
#    - Key insight: wage share ↓ → consumption ↓ → AD ↓ (if wage-led)
#
# Author: Ilan Strauss | AI Disclosures Project
# Date: January 2026
# =============================================================================

library(tidyverse)

# --- CONFIGURATION ---
DATA_DIR <- dirname(dirname(rstudioapi::getSourceEditorContext()$path))
# If not in RStudio, use:
# DATA_DIR <- here::here()

CROSSWALK_FILE <- file.path(DATA_DIR, "processed", "master_task_crosswalk_with_wages.csv")
OUTPUT_DIR <- file.path(DATA_DIR, "analysis")
dir.create(OUTPUT_DIR, showWarnings = FALSE)

# Kaleckian parameters (from literature: Stockhammer 2011, Onaran & Galanis 2014)
C_W <- 0.80   # Marginal propensity to consume out of wages
C_PI <- 0.40  # Marginal propensity to consume out of profits
AVG_C <- 0.70 # Aggregate consumption propensity (for multiplier)

# Acemoglu-Restrepo parameter
SIGMA <- 1.5  # Elasticity of substitution between tasks


# =============================================================================
# LOAD DATA
# =============================================================================

df <- read_csv(CROSSWALK_FILE, show_col_types = FALSE)


# =============================================================================
# CALCULATE OCCUPATION-LEVEL EXPOSURE
# =============================================================================
# Aggregate task-level data to occupation level
# AI exposure = share of total API usage attributable to that occupation

total_usage <- sum(df$api_usage_count, na.rm = TRUE)

df <- df %>%
  mutate(
    task_usage_share = api_usage_count / total_usage,
    # Weight by task importance (standard in labor economics)
    weighted_exposure = task_usage_share * coalesce(task_importance, mean(task_importance, na.rm = TRUE))
  )

# Aggregate to occupation level
occ <- df %>%
  group_by(onet_soc_code) %>%
  summarise(
    api_usage_count = sum(api_usage_count, na.rm = TRUE),
    task_usage_share = sum(task_usage_share, na.rm = TRUE),
    weighted_exposure = sum(weighted_exposure, na.rm = TRUE),
    A_MEAN = first(A_MEAN),
    A_MEDIAN = first(A_MEDIAN),
    TOT_EMP = first(TOT_EMP),
    onet_occupation_title = first(onet_occupation_title),
    Job_Zone = first(`Job Zone`),
    nonroutine_total = mean(nonroutine_total, na.rm = TRUE),
    task_importance = mean(task_importance, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(ai_exposure = task_usage_share) %>%
  filter(!is.na(A_MEAN))


# =============================================================================
# MODEL 1: ACEMOGLU-RESTREPO TASK DISPLACEMENT
# =============================================================================
# Theory: Production uses continuum of tasks. AI automates some,
# creating displacement effect on labor demand.
#
# Key equation: Δln(w) = -[(σ-1)/σ] × task_displacement_share

occ <- occ %>%
  mutate(
    wage_bill = TOT_EMP * A_MEAN,
    wage_share = wage_bill / sum(wage_bill, na.rm = TRUE),
    emp_share = TOT_EMP / sum(TOT_EMP, na.rm = TRUE)
  )

total_wage_bill <- sum(occ$wage_bill, na.rm = TRUE)

# Task displacement share (wage-weighted)
task_displacement_share <- sum(occ$wage_share * occ$ai_exposure, na.rm = TRUE)

# Employment-weighted exposure
emp_weighted_exposure <- sum(occ$emp_share * occ$ai_exposure, na.rm = TRUE)

# Wage effect using Acemoglu-Restrepo formula
wage_effect <- -((SIGMA - 1) / SIGMA) * task_displacement_share

ar_results <- list(
  task_displacement_share = task_displacement_share,
  emp_weighted_exposure = emp_weighted_exposure,
  wage_effect = wage_effect,
  sigma = SIGMA,
  total_wage_bill = total_wage_bill
)


# =============================================================================
# MODEL 2: KALECKIAN WAGE SHARE / AGGREGATE DEMAND
# =============================================================================
# Theory: Aggregate demand depends on income distribution.
# C = c_w × W + c_π × Π, where c_w > c_π (workers spend more)
#
# If wage share falls: consumption falls, AD falls (in wage-led regime).
# Keynesian multiplier amplifies the effect.

occ <- occ %>%
  mutate(
    wage_at_risk = wage_bill * ai_exposure,
    emp_at_risk = TOT_EMP * ai_exposure
  )

wage_at_risk_total <- sum(occ$wage_at_risk, na.rm = TRUE)
wage_share_effect <- wage_at_risk_total / total_wage_bill

# Consumption effect: ΔC = (c_w - c_π) × Δω
consumption_effect <- (C_W - C_PI) * wage_share_effect

# Keynesian multiplier: κ = 1/(1-c)
multiplier <- 1 / (1 - AVG_C)

# Total AD effect with multiplier
ad_effect <- consumption_effect * multiplier

# Employment at risk
total_emp <- sum(occ$TOT_EMP, na.rm = TRUE)
emp_at_risk_total <- sum(occ$emp_at_risk, na.rm = TRUE)

kalecki_results <- list(
  wage_at_risk = wage_at_risk_total,
  wage_share_effect = wage_share_effect,
  consumption_effect = consumption_effect,
  multiplier = multiplier,
  ad_effect = ad_effect,
  emp_at_risk = emp_at_risk_total,
  emp_share_at_risk = emp_at_risk_total / total_emp,
  c_w = C_W,
  c_pi = C_PI
)


# =============================================================================
# ROUTINE vs NON-ROUTINE ANALYSIS
# =============================================================================
# Traditional view (Autor et al. 2003): automation affects ROUTINE tasks.
# LLMs may reverse this by affecting NON-ROUTINE COGNITIVE tasks.

occ <- occ %>%
  mutate(routine_intensity = 1 - nonroutine_total)

valid_routine <- occ %>% filter(!is.na(routine_intensity))

routine_correlation <- cor(
  valid_routine$routine_intensity,
  valid_routine$ai_exposure,
  use = "complete.obs"
)

median_routine <- median(valid_routine$routine_intensity, na.rm = TRUE)

routine_jobs <- valid_routine %>% filter(routine_intensity >= median_routine)
nonroutine_jobs <- valid_routine %>% filter(routine_intensity < median_routine)

routine_results <- list(
  correlation = routine_correlation,
  routine_mean_exposure = mean(routine_jobs$ai_exposure, na.rm = TRUE),
  nonroutine_mean_exposure = mean(nonroutine_jobs$ai_exposure, na.rm = TRUE),
  routine_mean_wage = mean(routine_jobs$A_MEAN, na.rm = TRUE),
  nonroutine_mean_wage = mean(nonroutine_jobs$A_MEAN, na.rm = TRUE)
)


# =============================================================================
# DISTRIBUTIONAL ANALYSIS
# =============================================================================
# AI exposure by wage quintile

occ <- occ %>%
  mutate(wage_quintile = ntile(A_MEAN, 5))

quintile_analysis <- occ %>%
  group_by(wage_quintile) %>%
  summarise(
    ai_exposure = mean(ai_exposure, na.rm = TRUE),
    TOT_EMP = sum(TOT_EMP, na.rm = TRUE),
    A_MEAN = mean(A_MEAN, na.rm = TRUE),
    wage_at_risk = sum(wage_at_risk, na.rm = TRUE),
    .groups = "drop"
  )


# =============================================================================
# SAVE RESULTS
# =============================================================================

# Occupation-level file
write_csv(occ, file.path(OUTPUT_DIR, "occupation_ai_exposure.csv"))

# Model summary
model_summary <- tibble(
  Model = c("Acemoglu-Restrepo", "Acemoglu-Restrepo", "Kaleckian", "Kaleckian", "Kaleckian"),
  Metric = c(
    "Wage-weighted task displacement",
    sprintf("Predicted wage effect (σ=%.1f)", SIGMA),
    "Wage share reduction",
    "AD effect (wage-led, with multiplier)",
    "Employment share at risk"
  ),
  Value = c(
    ar_results$task_displacement_share,
    ar_results$wage_effect,
    kalecki_results$wage_share_effect,
    kalecki_results$ad_effect,
    kalecki_results$emp_share_at_risk
  ),
  Percent = c(
    sprintf("%.2f%%", ar_results$task_displacement_share * 100),
    sprintf("%.2f%%", ar_results$wage_effect * 100),
    sprintf("%.2f%%", kalecki_results$wage_share_effect * 100),
    sprintf("%.2f%%", kalecki_results$ad_effect * 100),
    sprintf("%.2f%%", kalecki_results$emp_share_at_risk * 100)
  )
)

write_csv(model_summary, file.path(OUTPUT_DIR, "model_summary.csv"))
