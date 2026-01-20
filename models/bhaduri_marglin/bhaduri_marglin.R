# =============================================================================
# Bhaduri-Marglin Endogenous Regime Model
# =============================================================================
#
# Post-Keynesian model with investment responding to both capacity utilization
# AND profit share. Endogenously determines wage-led vs profit-led regime.
#
# Investment function: I = g₀ + g_u×u + g_π×π
# Equilibrium: u* = (g₀ + g_π×π) / (s_π×π - g_u)
#
# Author: Ilan Strauss | AI Disclosures Project
# Date: January 2026
# =============================================================================

library(tidyverse)

# --- CONFIGURATION ---
SCRIPT_DIR <- tryCatch(
  dirname(rstudioapi::getSourceEditorContext()$path),
  error = function(e) here::here("models", "bhaduri_marglin")
)
ROOT_DIR <- dirname(dirname(SCRIPT_DIR))
DATA_DIR <- file.path(ROOT_DIR, "data")
CROSSWALK_FILE <- file.path(DATA_DIR, "processed", "master_task_crosswalk_with_wages.csv")
OUTPUT_DIR <- file.path(SCRIPT_DIR, "output")
dir.create(OUTPUT_DIR, showWarnings = FALSE)

# Model parameters (from literature: Stockhammer 2017, Onaran & Galanis 2014)
S_PI <- 0.45  # Propensity to save out of profits (s_π)
G_U <- 0.10   # Investment sensitivity to capacity utilization (g_u)
G_PI <- 0.05  # Investment sensitivity to profit share (g_π)
G_0 <- 0.03   # Autonomous investment rate (g₀)
U_BASELINE <- 0.80  # Baseline capacity utilization (80%)
WAGE_SHARE_BASELINE <- 0.55  # Approximate US wage share


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
# BHADURI-MARGLIN MODEL
# =============================================================================

occ <- occ %>%
  mutate(wage_bill = TOT_EMP * A_MEAN)

total_wage_bill <- sum(occ$wage_bill, na.rm = TRUE)

# Wage at risk
occ <- occ %>%
  mutate(wage_at_risk = wage_bill * ai_exposure)

# Profit share calculations
profit_share_baseline <- 1 - WAGE_SHARE_BASELINE
delta_profit_share <- sum(occ$wage_at_risk, na.rm = TRUE) / total_wage_bill
profit_share_new <- profit_share_baseline + delta_profit_share

# Equilibrium utilization BEFORE AI shock
denominator_before <- (S_PI * profit_share_baseline) - G_U
if (denominator_before <= 0) {
  u_star_before <- U_BASELINE
} else {
  u_star_before <- (G_0 + G_PI * profit_share_baseline) / denominator_before
}

# Equilibrium utilization AFTER AI shock
denominator_after <- (S_PI * profit_share_new) - G_U
if (denominator_after <= 0) {
  u_star_after <- U_BASELINE
} else {
  u_star_after <- (G_0 + G_PI * profit_share_new) / denominator_after
}

# Change in utilization
delta_u <- u_star_after - u_star_before

# Regime determination: ∂u*/∂π
regime_numerator <- -(G_PI * G_U + G_0 * S_PI)
regime_denominator <- ifelse(denominator_before > 0, denominator_before^2, 1)
partial_u_partial_pi <- regime_numerator / regime_denominator

regime <- ifelse(partial_u_partial_pi > 0, "profit-led", "wage-led")

# Output effect
output_effect <- delta_u / U_BASELINE

# Investment effect: ΔI = g_u×Δu + g_π×Δπ
investment_effect <- G_U * delta_u + G_PI * delta_profit_share

# Savings effect: ΔS = s_π×(π×Δu + u×Δπ)
savings_effect <- S_PI * (profit_share_baseline * delta_u + U_BASELINE * delta_profit_share)

results <- list(
  profit_share_baseline = profit_share_baseline,
  profit_share_new = profit_share_new,
  delta_profit_share = delta_profit_share,
  u_star_before = u_star_before,
  u_star_after = u_star_after,
  delta_utilization = delta_u,
  partial_u_partial_pi = partial_u_partial_pi,
  regime = regime,
  output_effect = output_effect,
  investment_effect = investment_effect,
  savings_effect = savings_effect,
  total_wage_bill = total_wage_bill,
  s_pi = S_PI,
  g_u = G_U,
  g_pi = G_PI,
  g_0 = G_0
)


# =============================================================================
# SAVE RESULTS
# =============================================================================

# Occupation-level exposure
write_csv(occ, file.path(OUTPUT_DIR, "occupation_exposure.csv"))

# Model summary
model_summary <- tibble(
  Metric = c(
    "Baseline profit share",
    "New profit share (post-AI)",
    "Change in profit share",
    "Equilibrium utilization (before)",
    "Equilibrium utilization (after)",
    "Change in utilization",
    "Demand regime",
    "Output effect",
    "∂u*/∂π (regime indicator)"
  ),
  Value = c(
    results$profit_share_baseline,
    results$profit_share_new,
    results$delta_profit_share,
    results$u_star_before,
    results$u_star_after,
    results$delta_utilization,
    NA_real_,
    results$output_effect,
    results$partial_u_partial_pi
  ),
  Formatted = c(
    sprintf("%.1f%%", results$profit_share_baseline * 100),
    sprintf("%.1f%%", results$profit_share_new * 100),
    sprintf("%.2f%%", results$delta_profit_share * 100),
    sprintf("%.1f%%", results$u_star_before * 100),
    sprintf("%.1f%%", results$u_star_after * 100),
    sprintf("%.2f%%", results$delta_utilization * 100),
    results$regime,
    sprintf("%.2f%%", results$output_effect * 100),
    sprintf("%.4f", results$partial_u_partial_pi)
  )
)

write_csv(model_summary, file.path(OUTPUT_DIR, "model_results.csv"))

# Parameters used
params <- tibble(
  Parameter = c("s_π", "g_u", "g_π", "g₀", "u_baseline", "wage_share_baseline"),
  Value = c(S_PI, G_U, G_PI, G_0, U_BASELINE, WAGE_SHARE_BASELINE),
  Description = c(
    "Propensity to save out of profits",
    "Investment sensitivity to utilization",
    "Investment sensitivity to profit share",
    "Autonomous investment rate",
    "Baseline capacity utilization",
    "Baseline wage share"
  )
)

write_csv(params, file.path(OUTPUT_DIR, "parameters.csv"))
