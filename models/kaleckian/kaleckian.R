# =============================================================================
# Kaleckian Wage Share / Aggregate Demand Model
# =============================================================================
#
# Post-Keynesian demand-side framework analyzing how AI-driven income
# redistribution affects aggregate demand through consumption channels.
#
# Key insight: c_w > c_π → wage share ↓ → consumption ↓ → AD ↓
#
# Author: Ilan Strauss | AI Disclosures Project
# Date: January 2026
# =============================================================================

library(tidyverse)

# --- CONFIGURATION ---
SCRIPT_DIR <- tryCatch(
  dirname(rstudioapi::getSourceEditorContext()$path),
  error = function(e) here::here("models", "kaleckian")
)
ROOT_DIR <- dirname(dirname(SCRIPT_DIR))
DATA_DIR <- file.path(ROOT_DIR, "data")
CROSSWALK_FILE <- file.path(DATA_DIR, "processed", "master_task_crosswalk_with_wages.csv")
OUTPUT_DIR <- file.path(SCRIPT_DIR, "output")
dir.create(OUTPUT_DIR, showWarnings = FALSE)

# Model parameters (from literature: Stockhammer 2011, Onaran & Galanis 2014)
C_W <- 0.80   # Marginal propensity to consume out of wages
C_PI <- 0.40  # Marginal propensity to consume out of profits
AVG_C <- 0.70 # Aggregate consumption propensity (for multiplier)


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
# KALECKIAN MODEL
# =============================================================================

occ <- occ %>%
  mutate(
    wage_bill = TOT_EMP * A_MEAN
  )

total_wage_bill <- sum(occ$wage_bill, na.rm = TRUE)

# Wage bill at risk (exposure-weighted)
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

results <- list(
  wage_at_risk = wage_at_risk_total,
  wage_share_effect = wage_share_effect,
  consumption_effect = consumption_effect,
  multiplier = multiplier,
  ad_effect = ad_effect,
  emp_at_risk = emp_at_risk_total,
  emp_share_at_risk = emp_at_risk_total / total_emp,
  total_wage_bill = total_wage_bill,
  c_w = C_W,
  c_pi = C_PI
)


# =============================================================================
# SAVE RESULTS
# =============================================================================

# Occupation-level exposure
write_csv(occ, file.path(OUTPUT_DIR, "occupation_exposure.csv"))

# Model summary
model_summary <- tibble(
  Metric = c(
    "Wage share reduction",
    "Consumption effect",
    sprintf("Keynesian multiplier (c=%.2f)", AVG_C),
    "AD effect (with multiplier)",
    "Employment share at risk",
    "Wage bill at risk ($)"
  ),
  Value = c(
    results$wage_share_effect,
    results$consumption_effect,
    results$multiplier,
    results$ad_effect,
    results$emp_share_at_risk,
    results$wage_at_risk
  ),
  Percent = c(
    sprintf("%.2f%%", results$wage_share_effect * 100),
    sprintf("%.2f%%", results$consumption_effect * 100),
    sprintf("%.2f", results$multiplier),
    sprintf("%.2f%%", results$ad_effect * 100),
    sprintf("%.2f%%", results$emp_share_at_risk * 100),
    sprintf("$%s", format(results$wage_at_risk, big.mark = ",", scientific = FALSE))
  )
)

write_csv(model_summary, file.path(OUTPUT_DIR, "model_results.csv"))
