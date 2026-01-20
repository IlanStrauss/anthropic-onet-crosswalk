# =============================================================================
# Build Anthropic API Task → O*NET Crosswalk
# =============================================================================
#
# Links Anthropic Claude API task descriptions to O*NET occupational codes via:
# 1. Text normalization (lowercase, remove punctuation)
# 2. Exact string matching
# 3. Fuzzy matching (Levenshtein, threshold >= 85)
# 4. Enrichment with O*NET occupation attributes
#
# Author: Ilan Strauss | AI Disclosures Project
# Date: January 2026
# =============================================================================

library(tidyverse)
library(stringdist)  # For fuzzy matching

# --- CONFIGURATION ---
BASE_DIR <- dirname(dirname(rstudioapi::getSourceEditorContext()$path))
# If not in RStudio, use:
# BASE_DIR <- here::here()

RAW_DIR <- file.path(BASE_DIR, "raw")
PROCESSED_DIR <- file.path(BASE_DIR, "processed")
ANTHROPIC_DATA <- file.path(BASE_DIR, "..", "release_2026_01_15", "data", "intermediate",
                            "aei_raw_1p_api_2025-11-13_to_2025-11-20.csv")
ONET_DIR <- file.path(RAW_DIR, "db_29_1_text")

FUZZY_THRESHOLD <- 85  # Minimum similarity score (0-100)


# =============================================================================
# TEXT NORMALIZATION
# =============================================================================
# Lowercase, remove punctuation, collapse whitespace

normalize_text <- function(text) {
  text %>%
    tolower() %>%
    str_trim() %>%
    str_replace_all("[^[:alnum:][:space:]]", "") %>%
    str_replace_all("\\s+", " ")
}


# =============================================================================
# LOAD DATA
# =============================================================================

load_data <- function() {
  anthropic <- read_csv(ANTHROPIC_DATA, show_col_types = FALSE)

  onet_tasks <- read_tsv(file.path(ONET_DIR, "Task Statements.txt"), show_col_types = FALSE)
  onet_occs <- read_tsv(file.path(ONET_DIR, "Occupation Data.txt"), show_col_types = FALSE)
  job_zones <- read_tsv(file.path(ONET_DIR, "Job Zones.txt"), show_col_types = FALSE)
  education <- read_tsv(file.path(ONET_DIR, "Education, Training, and Experience.txt"), show_col_types = FALSE)

  list(
    anthropic = anthropic,
    onet_tasks = onet_tasks,
    onet_occs = onet_occs,
    job_zones = job_zones,
    education = education
  )
}


# =============================================================================
# EXTRACT ANTHROPIC TASKS
# =============================================================================
# Filter to O*NET task facet and extract task descriptions with API counts

extract_anthropic_tasks <- function(anthropic) {
  anthropic %>%
    filter(facet == "onet_task", variable == "onet_task_count") %>%
    select(anthropic_task = cluster_name, api_count = value) %>%
    filter(!tolower(anthropic_task) %in% c("not_classified", "none")) %>%
    mutate(task_norm = normalize_text(anthropic_task))
}


# =============================================================================
# EXACT MATCHING
# =============================================================================
# Match normalized Anthropic tasks to O*NET tasks via exact string comparison

exact_match <- function(task_data, onet_tasks) {
  # Normalize O*NET tasks
  onet_tasks <- onet_tasks %>%
    mutate(task_norm = normalize_text(Task))

  # Create lookup (first occurrence per normalized text)
  onet_lookup <- onet_tasks %>%
    group_by(task_norm) %>%
    slice(1) %>%
    ungroup() %>%
    select(task_norm, `O*NET-SOC Code`, `Task ID`, Task, `Task Type`)

  # Join
  merged <- task_data %>%
    left_join(onet_lookup, by = "task_norm")

  # Split matched and unmatched
  matched <- merged %>%
    filter(!is.na(`O*NET-SOC Code`)) %>%
    mutate(match_method = "exact", match_score = 100)

  unmatched <- merged %>%
    filter(is.na(`O*NET-SOC Code`)) %>%
    select(anthropic_task, api_count, task_norm)

  list(matched = matched, unmatched = unmatched, onet_tasks = onet_tasks)
}


# =============================================================================
# FUZZY MATCHING
# =============================================================================
# Match remaining tasks using Levenshtein similarity

fuzzy_match <- function(unmatched, onet_tasks, threshold = FUZZY_THRESHOLD) {
  # Get unique O*NET normalized tasks
  onet_lookup <- onet_tasks %>%
    group_by(task_norm) %>%
    slice(1) %>%
    ungroup()

  onet_choices <- unique(onet_lookup$task_norm)

  # Match each unmatched task
  fuzzy_results <- map_dfr(seq_len(nrow(unmatched)), function(i) {
    query <- unmatched$task_norm[i]

    # Calculate Levenshtein similarity (convert distance to 0-100 score)
    distances <- stringdist(query, onet_choices, method = "lv")
    max_len <- pmax(nchar(query), nchar(onet_choices))
    scores <- 100 * (1 - distances / max_len)

    best_idx <- which.max(scores)
    best_score <- scores[best_idx]

    if (best_score >= threshold) {
      best_match <- onet_choices[best_idx]
      onet_row <- onet_lookup %>% filter(task_norm == best_match) %>% slice(1)

      tibble(
        anthropic_task = unmatched$anthropic_task[i],
        api_count = unmatched$api_count[i],
        task_norm = query,
        `O*NET-SOC Code` = onet_row$`O*NET-SOC Code`,
        `Task ID` = onet_row$`Task ID`,
        Task = onet_row$Task,
        `Task Type` = onet_row$`Task Type`,
        match_method = "fuzzy",
        match_score = best_score
      )
    } else {
      NULL
    }
  })

  fuzzy_results
}


# =============================================================================
# ENRICH WITH O*NET ATTRIBUTES
# =============================================================================
# Add occupation titles, job zones, and typical education

enrich_with_onet <- function(matched, onet_occs, job_zones, education) {
  # Add occupation titles and descriptions
  matched <- matched %>%
    left_join(
      onet_occs %>% select(`O*NET-SOC Code`, Title, Description),
      by = "O*NET-SOC Code"
    )

  # Add job zones (1-5 education/preparation scale)
  jz_clean <- job_zones %>%
    select(`O*NET-SOC Code`, `Job Zone`) %>%
    distinct()

  matched <- matched %>%
    left_join(jz_clean, by = "O*NET-SOC Code")

  # Add typical education level
  edu_level <- education %>%
    filter(`Element Name` == "Required Level of Education") %>%
    select(`O*NET-SOC Code`, Category, `Data Value`)

  if (nrow(edu_level) > 0) {
    edu_pivot <- edu_level %>%
      pivot_wider(names_from = Category, values_from = `Data Value`, values_fn = first)

    edu_cols <- setdiff(names(edu_pivot), "O*NET-SOC Code")
    if (length(edu_cols) > 0) {
      edu_pivot <- edu_pivot %>%
        rowwise() %>%
        mutate(
          typical_education = edu_cols[which.max(c_across(all_of(edu_cols)))],
          typical_education_pct = max(c_across(all_of(edu_cols)), na.rm = TRUE)
        ) %>%
        ungroup() %>%
        select(`O*NET-SOC Code`, typical_education, typical_education_pct)

      matched <- matched %>%
        left_join(edu_pivot, by = "O*NET-SOC Code")
    }
  }

  matched
}


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

save_outputs <- function(matched, task_data, output_dir) {
  # Rename and select final columns
  final <- matched %>%
    select(
      anthropic_task_description = anthropic_task,
      api_usage_count = api_count,
      onet_soc_code = `O*NET-SOC Code`,
      onet_task_id = `Task ID`,
      onet_task_description = Task,
      onet_task_type = `Task Type`,
      onet_occupation_title = Title,
      onet_occupation_description = Description,
      match_method,
      match_score,
      job_zone = `Job Zone`,
      typical_education,
      typical_education_pct
    ) %>%
    arrange(desc(api_usage_count))

  write_csv(final, file.path(output_dir, "master_task_crosswalk.csv"))

  # Save unmatched tasks
  matched_tasks <- unique(matched$anthropic_task)
  unmatched_final <- task_data %>%
    filter(!anthropic_task %in% matched_tasks) %>%
    select(anthropic_task, api_count) %>%
    arrange(desc(api_count))

  write_csv(unmatched_final, file.path(output_dir, "unmatched_tasks.csv"))

  list(final = final, unmatched = unmatched_final)
}


# =============================================================================
# MAIN EXECUTION
# =============================================================================

main <- function() {
  # Load data
  data <- load_data()

  # Extract Anthropic tasks
  task_data <- extract_anthropic_tasks(data$anthropic)

  # Exact matching
  exact_results <- exact_match(task_data, data$onet_tasks)

  # Fuzzy matching (this may take a few minutes)
  fuzzy_matched <- fuzzy_match(exact_results$unmatched, exact_results$onet_tasks)

  # Combine matches
  all_matched <- bind_rows(exact_results$matched, fuzzy_matched)

  # Enrich with O*NET attributes
  enriched <- enrich_with_onet(all_matched, data$onet_occs, data$job_zones, data$education)

  # Save outputs
  save_outputs(enriched, task_data, PROCESSED_DIR)
}

# Run if executed directly
if (sys.nframe() == 0) {
  main()
}
