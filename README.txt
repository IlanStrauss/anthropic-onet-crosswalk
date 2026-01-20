================================================================================
ANTHROPIC API TASK → O*NET CROSSWALK DATASET
================================================================================

Project: AI Disclosures Project
Author: Ilan Strauss
Date: January 2026
Contact: ilan@aidisclosures.org

================================================================================
WHAT THIS IS
================================================================================

This dataset links Anthropic's Claude API task classifications to the U.S.
Department of Labor's O*NET occupational taxonomy. It enables analysis of
AI usage patterns by standardized occupation codes (SOC), which can then be
linked to wage data, employment statistics, and other labor market indicators.

================================================================================
WHY WE BUILT THIS
================================================================================

Anthropic's Economic Index (January 2026) provides data on how Claude is used,
classified into O*NET task descriptions. However, Anthropic only provides the
task description text, not the O*NET task IDs or occupation codes.

This crosswalk recovers the linkage, enabling researchers to:
- Analyze API usage by occupation
- Link to BLS wage and employment data
- Compare with AI exposure indices (Webb, Felten, Eloundou et al.)
- Study which occupations/tasks are most affected by AI

================================================================================
DATA SOURCES
================================================================================

1. ANTHROPIC ECONOMIC INDEX (November 2025 data)
   - Source: https://huggingface.co/datasets/Anthropic/EconomicIndex
   - File: aei_raw_1p_api_2025-11-13_to_2025-11-20.csv
   - Contains: 1M API transcript classifications into O*NET tasks
   - Variables: task descriptions, usage counts, and other primitives

2. O*NET DATABASE v29.1 (October 2024)
   - Source: https://www.onetcenter.org/database.html
   - Contains: 18,796 task statements across 1,016 occupations
   - Provides: SOC codes, task IDs, occupation titles, job zones,
     education requirements, skills, abilities, work context

================================================================================
METHODOLOGY
================================================================================

STEP 1: TEXT NORMALIZATION
- Convert to lowercase
- Remove punctuation
- Normalize whitespace
- This handles minor formatting differences between sources

STEP 2: EXACT MATCHING
- Match Anthropic task descriptions to O*NET task statements
- Using normalized text comparison
- Result: 1,998 exact matches

STEP 3: FUZZY MATCHING (for remaining unmatched)
- Algorithm: rapidfuzz library, ratio scorer
- Threshold: >= 85 (conservative, high quality)
- Validated by manual review of match quality
- Result: 113 additional fuzzy matches

STEP 4: ENRICHMENT
- Link matched tasks to O*NET occupation codes (SOC)
- Add occupation titles and descriptions
- Add Job Zone (1-5 skill/education level)
- Add typical education requirements

STEP 5: QUALITY CONTROL
- Exclude placeholder categories ("not_classified", "none")
- Manual review of fuzzy matches at different thresholds
- Document unmatched tasks for transparency

================================================================================
FOLDER STRUCTURE
================================================================================

data/onet/
├── README.txt                    # This file
├── raw/
│   ├── onet_db.zip              # Original O*NET download
│   └── db_29_1_text/            # Extracted O*NET files
│       ├── Task Statements.txt
│       ├── Occupation Data.txt
│       ├── Job Zones.txt
│       ├── Education, Training, and Experience.txt
│       └── ... (other O*NET files)
├── processed/
│   ├── master_task_crosswalk.csv    # MAIN OUTPUT FILE
│   ├── unmatched_tasks.csv          # Tasks that couldn't be matched
│   ├── fuzzy_matches_review.csv     # Fuzzy match scores for QA
│   ├── api_usage_by_occupation.csv  # Aggregated by occupation
│   └── api_usage_by_task.csv        # Task-level with SOC codes
└── scripts/
    └── build_crosswalk.py           # Reproducible build script

================================================================================
MAIN OUTPUT: master_task_crosswalk.csv
================================================================================

COLUMNS:
- anthropic_task_description: Original task text from Anthropic
- api_usage_count: Number of API calls for this task
- onet_soc_code: O*NET-SOC occupation code (e.g., "15-1252.00")
- onet_task_id: O*NET task ID
- onet_task_description: Official O*NET task text
- onet_task_type: Core or Supplemental task
- onet_occupation_title: Occupation name (e.g., "Software Developers")
- onet_occupation_description: Full occupation description
- match_method: "exact" or "fuzzy"
- match_score: 100 for exact, fuzzy score (85-100) for fuzzy
- job_zone: 1-5 skill level (1=little prep, 5=extensive prep)
- typical_education: Most common education level
- typical_education_pct: Percentage with that education level

================================================================================
MATCH QUALITY SUMMARY
================================================================================

Total Anthropic tasks (excluding placeholders): 2,251
Matched tasks: 2,111
Match rate: 93.8%

API usage coverage: 96.8%
(The matched tasks account for 96.8% of all API task usage)

Match method breakdown:
- Exact matches: 1,998 (94.6%)
- Fuzzy matches: 113 (5.4%)

Unique occupations covered: 562

Unmatched tasks: 140 (accounting for only 3.2% of API usage)

================================================================================
LINKING TO OTHER DATA
================================================================================

With SOC codes, you can link to:

1. BLS WAGE DATA
   - Occupational Employment and Wage Statistics (OEWS)
   - National/state/metro area wages by occupation

2. EMPLOYMENT PROJECTIONS
   - BLS Employment Projections program
   - 10-year growth forecasts by occupation

3. AI EXPOSURE INDICES
   - Webb (2020): AI patent-based exposure
   - Felten et al. (2021): AI capability-based exposure
   - Eloundou et al. (2023): GPT exposure scores

4. O*NET ATTRIBUTES
   - Skills, abilities, knowledge requirements
   - Work context and work styles
   - Related occupations

================================================================================
LIMITATIONS
================================================================================

1. 140 tasks (3.2% of usage) could not be matched
   - Some may be Anthropic-specific classifications
   - Some may have text differences too large for fuzzy matching

2. Many-to-many mapping
   - Same task can appear in multiple occupations
   - We take first match; could aggregate differently

3. O*NET version
   - Using v29.1 (October 2024)
   - Anthropic may use different version

4. API data only
   - Does not include Claude.ai consumer data
   - 74% work-related vs 46% on Claude.ai

================================================================================
CITATION
================================================================================

If using this crosswalk, please cite:

Strauss, I. (2026). "Anthropic API Task to O*NET Crosswalk Dataset."
AI Disclosures Project. https://github.com/IlanStrauss/anthropic-econ-critique

Data sources:
- Anthropic. (2026). "Anthropic Economic Index."
  https://huggingface.co/datasets/Anthropic/EconomicIndex
- O*NET Resource Center. (2024). "O*NET Database v29.1."
  https://www.onetcenter.org/database.html

================================================================================
