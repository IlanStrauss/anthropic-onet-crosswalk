# =============================================================================
# Acemoglu-Restrepo Task Displacement Model
# =============================================================================
#
# Neoclassical task-based framework for analyzing AI's labor market effects.
# Key equation: Δln(w) = -[(σ-1)/σ] × task_displacement_share
#
# Author: Ilan Strauss | AI Disclosures Project
# Date: January 2026
# =============================================================================

library(tidyverse)

# --- CONFIGURATION ---
SCRIPT_DIR <- tryCatch(
  dirname(rstudioapi::getSourceEditorContext()$path),
  error = function(e) here::here("models", "acemoglu_restrepo")
)
ROOT_DIR <- dirname(dirname(SCRIPT_DIR))
DATA_DIR <- file.path(ROOT_DIR, "data")
CROSSWALK_FILE <- file.path(DATA_DIR, "processed", "master_task_crosswalk_with_wages.csv")
OUTPUT_DIR <- file.path(SCRIPT_DIR, "output")
dir.create(OUTPUT_DIR, showWarnings = FALSE)

# Model parameter
SIGMA <- 1.5  # Elasticity of substitution between tasks


# =============================================================================
# LOAD AND PREPARE DATA
# =============================================================================

df <- read_csv(CROSSWALK_FILE, show_col_types = FALSE)

total_usage <- sum(df$api_usage_count, na.rm = TRUE)

df <- df %>%
  mutate(
    task_usage_share = api_usage_count / total_usage,
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
# ACEMOGLU-RESTREPO MODEL
# =============================================================================

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

results <- list(
  task_displacement_share = task_displacement_share,
  emp_weighted_exposure = emp_weighted_exposure,
  wage_effect = wage_effect,
  sigma = SIGMA,
  total_wage_bill = total_wage_bill
)


# =============================================================================
# SAVE RESULTS
# =============================================================================

# Occupation-level exposure
write_csv(occ, file.path(OUTPUT_DIR, "occupation_exposure.csv"))

# Model summary
model_summary <- tibble(
  Metric = c(
    "Wage-weighted task displacement",
    sprintf("Predicted wage effect (σ=%.1f)", SIGMA),
    "Employment-weighted exposure",
    "Total wage bill ($)"
  ),
  Value = c(
    results$task_displacement_share,
    results$wage_effect,
    results$emp_weighted_exposure,
    results$total_wage_bill
  ),
  Percent = c(
    sprintf("%.2f%%", results$task_displacement_share * 100),
    sprintf("%.2f%%", results$wage_effect * 100),
    sprintf("%.2f%%", results$emp_weighted_exposure * 100),
    sprintf("$%s", format(results$total_wage_bill, big.mark = ",", scientific = FALSE))
  )
)

write_csv(model_summary, file.path(OUTPUT_DIR, "model_results.csv"))
