# Anthropic API → O*NET → BLS Crosswalk Dataset

**Author:** Ilan Strauss | AI Disclosures Project
**Date:** January 2026
**Contact:** ilan@aidisclosures.org
**Repository:** https://github.com/IlanStrauss/anthropic-onet-crosswalk

---

## Executive Summary

This dataset links Anthropic's Claude API task-level usage data to:
1. **O\*NET** occupational task taxonomy (SOC codes, task attributes)
2. **BLS** wage and employment statistics

**Why this matters:** Anthropic released task-level API usage data but only provided task description text—not standardized occupation codes. Without SOC codes, researchers cannot link to wage data, employment statistics, or established AI exposure indices. This crosswalk recovers that linkage, enabling rigorous labor economics analysis.

**Key output:** `processed/master_task_crosswalk_with_wages.csv` (2,111 rows × 38 columns)

---

## 1. Data Sources

### 1.1 Anthropic Economic Index

| Attribute | Value |
|-----------|-------|
| **Source** | Anthropic Economic Index |
| **Coverage period** | November 13-20, 2025 |
| **Access date** | January 2026 |
| **URL** | https://huggingface.co/datasets/Anthropic/EconomicIndex |
| **File used** | `aei_raw_1p_api_2025-11-13_to_2025-11-20.csv` |
| **Data type** | First-party API usage logs |

**What Anthropic provides:**
- Task descriptions (text strings mapped to O\*NET task statements by Anthropic's classifier)
- Usage counts (number of API calls per task)
- Facet labels (`onet_task`, `use_case`, `ai_autonomy`, etc.)

**What Anthropic does NOT provide:**
- O\*NET task IDs
- SOC occupation codes
- Any numeric O\*NET identifiers

**Filtering applied:**
```python
# Extract O*NET task data only
df = df[(df['facet'] == 'onet_task') & (df['variable'] == 'onet_task_count')]
# Exclude placeholder values
df = df[~df['value'].isin(['not_classified', 'none'])]
```

**Result:** 2,253 unique task descriptions with API usage counts

### 1.2 O\*NET Database

| Attribute | Value |
|-----------|-------|
| **Source** | O\*NET Resource Center |
| **Version** | 29.1 |
| **Release date** | October 2024 |
| **URL** | https://www.onetcenter.org/database.html |
| **Download** | `db_29_1_text.zip` |

**O\*NET files used:**

| File | Purpose | Records |
|------|---------|---------|
| `Task Statements.txt` | Task descriptions with SOC codes | 19,265 tasks |
| `Occupation Data.txt` | Occupation titles and descriptions | 1,016 occupations |
| `Job Zones.txt` | Education/preparation levels | 1,016 occupations |
| `Education, Training, and Experience.txt` | Typical education | 1,016 occupations |
| `Task Ratings.txt` | Importance (IM) and Relevance (RT) scales | ~38,000 ratings |
| `Tasks to DWAs.txt` | Task → Detailed Work Activity mapping | ~85,000 mappings |
| `DWA Reference.txt` | DWA titles | 2,069 DWAs |
| `IWA Reference.txt` | Intermediate Work Activity mapping | 332 IWAs |
| `Work Activities.txt` | Generalized work activity scores | ~40,000 scores |

**Why O\*NET:** O\*NET is the standard occupational taxonomy used in labor economics. All major studies of AI labor market effects use O\*NET (Autor et al. 2003, Acemoglu & Autor 2011, Webb 2020, Felten et al. 2021, Eloundou et al. 2023).

### 1.3 BLS Occupational Employment and Wage Statistics (OEWS)

| Attribute | Value |
|-----------|-------|
| **Source** | U.S. Bureau of Labor Statistics |
| **Survey** | Occupational Employment and Wage Statistics |
| **Reference period** | May 2024 |
| **Access date** | January 2026 |
| **URL** | https://www.bls.gov/oes/tables.htm |
| **Download** | `oesm24all.zip` → `all_data_M_2024.xlsx` |

**Filtering applied:**
```python
# National cross-industry totals for detailed occupations only
national = bls[
    (bls['AREA'] == 99) &           # U.S. national
    (bls['NAICS'] == '000000') &    # Cross-industry
    (bls['I_GROUP'] == 'cross-industry') &
    (bls['O_GROUP'] == 'detailed')  # Detailed occupations only
]
```

**Result:** 831 detailed occupations with employment and wage data

**Why BLS OEWS:** OEWS is the standard source for occupation-level wage data in the U.S. It provides mean, median, and percentile wages by SOC code, enabling wage-weighted analysis of AI exposure.

---

## 2. Construction Methodology

### 2.1 Overview of Data Pipeline

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   ANTHROPIC API     │     │      O*NET DB       │     │      BLS OEWS       │
│   Task descriptions │     │   Task Statements   │     │   Wage/Employment   │
│   + usage counts    │     │   + SOC codes       │     │   by SOC code       │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           │    Text Matching          │                           │
           │    (exact + fuzzy)        │                           │
           └───────────┬───────────────┘                           │
                       │                                           │
                       ▼                                           │
              ┌─────────────────┐                                  │
              │  Matched Tasks  │                                  │
              │  with SOC codes │                                  │
              └────────┬────────┘                                  │
                       │                                           │
                       │  Enrich with O*NET attributes             │
                       │  (Job Zone, Task Ratings, DWAs,           │
                       │   Work Activities)                        │
                       │                                           │
                       ▼                                           │
              ┌─────────────────┐                                  │
              │ Enriched Tasks  │       SOC Code Join              │
              │ with O*NET data │◄─────────────────────────────────┘
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────────────────────────┐
              │  FINAL OUTPUT                       │
              │  master_task_crosswalk_with_wages   │
              │  (2,111 rows × 38 columns)          │
              └─────────────────────────────────────┘
```

### 2.2 Step 1: Text Normalization

**Problem:** Anthropic's task descriptions may differ slightly from O\*NET's official task statements (punctuation, capitalization, whitespace).

**Solution:** Normalize both sources before matching.

```python
import re

def normalize_text(text):
    """Normalize text for matching."""
    text = str(text).lower().strip()      # Lowercase
    text = re.sub(r'[^\w\s]', '', text)   # Remove punctuation
    text = re.sub(r'\s+', ' ', text)      # Normalize whitespace
    return text
```

**Applied to:**
- 2,253 Anthropic task descriptions
- 19,265 O\*NET task statements

### 2.3 Step 2: Exact Matching

**Method:** Direct string comparison of normalized text.

```python
# Create lookup dictionary
onet_lookup = {normalize_text(task): (soc_code, task_id, original_text)
               for task, soc_code, task_id, original_text in onet_tasks}

# Match
for anthropic_task in anthropic_tasks:
    normalized = normalize_text(anthropic_task)
    if normalized in onet_lookup:
        match = onet_lookup[normalized]
        # Record: exact match, score=100
```

**Result:** 1,998 exact matches (88.7% of Anthropic tasks)

### 2.4 Step 3: Fuzzy Matching

**Problem:** 255 Anthropic tasks did not exactly match any O\*NET task after normalization.

**Solution:** Fuzzy string matching for remaining unmatched tasks.

**Library:** `rapidfuzz` (faster alternative to `fuzzywuzzy`)

**Algorithm:** `fuzz.ratio` (Levenshtein distance-based similarity)

**Threshold:** ≥85 (conservative, validated by manual review)

```python
from rapidfuzz import fuzz, process

for anthropic_task in unmatched_tasks:
    normalized = normalize_text(anthropic_task)
    # Find best match in O*NET
    best_match, score, _ = process.extractOne(
        normalized,
        onet_normalized_tasks,
        scorer=fuzz.ratio
    )
    if score >= 85:
        # Record: fuzzy match with score
```

**Quality validation of threshold:**
| Score Range | Quality | Action |
|-------------|---------|--------|
| 95-100 | Near-identical (punctuation/formatting only) | Accept |
| 85-94 | Minor word variations, same semantic meaning | Accept |
| <85 | Potential false matches | Reject |

**Result:** 113 additional fuzzy matches (5.0% of matched tasks)

**Unmatched:** 142 tasks could not be matched (6.2% of Anthropic tasks, 3.2% of API usage)

### 2.5 Step 4: Handling Ambiguous Task→SOC Mappings

**Problem:** Some O\*NET task statements appear in multiple occupations with identical text. For example, "Maintain regularly scheduled office hours to advise and assist students" appears in 34 different professor occupations (25-1011 through 25-1199).

When an Anthropic task matches such a shared task statement, we cannot determine from the string alone which occupation generated the API call.

**Scope of ambiguity:**
| Metric | Value |
|--------|-------|
| O\*NET tasks shared across multiple SOCs | 414 (2.4% of O\*NET tasks) |
| Anthropic tasks matching ambiguous O\*NET tasks | 97 (4.6% of matched tasks) |
| API usage in ambiguous tasks | ~7% of total usage |

**Solution: Equal-split allocation (main specification)**

Because O\*NET task statements can be shared across multiple occupations, a subset of Anthropic task strings maps to multiple SOCs. We treat these mappings as ambiguous and allocate usage across candidate occupations using a **conservative equal-split rule**.

For each Anthropic task that matches N different SOC codes:
```python
# Create N rows, one per candidate SOC
for soc in candidate_socs:
    row['api_usage_count'] = original_count / N  # Equal split
    row['split_weight'] = 1 / N
    row['n_candidate_socs'] = N
    row['is_ambiguous'] = True
    row['ambiguous_group_id'] = unique_id  # For auditing
```

**Why equal-split:**
- **No additional assumptions:** The string alone does not identify the occupation; we do not inject a prior about which occupation generated the calls.
- **Conservation guaranteed:** Weights sum to 1, totals match, no inflation of usage.
- **Easy to explain:** Transparent and robust to downstream critiques.

**Robustness check: Employment-weighted allocation**

As a sensitivity analysis, we also provide employment-weighted allocation:
```python
# Weight by BLS employment within candidate SOC set
weight_s = employment_s / sum(employment in candidate_socs)
row['api_usage_count'] = original_count * weight_s
```

This assumes API usage is more likely from larger occupations. We report both specifications to demonstrate robustness.

**New fields in crosswalk:**

| Field | Type | Description |
|-------|------|-------------|
| `api_usage_count_original` | float | Original usage count before splitting |
| `api_usage_count` | float | Usage after equal-split allocation |
| `split_weight` | float | Weight applied (1/N for equal split) |
| `n_candidate_socs` | integer | Number of candidate SOCs for this task |
| `is_ambiguous` | boolean | True if task maps to multiple SOCs |
| `ambiguous_group_id` | integer | Unique ID for auditing ambiguous groups |

**Audit outputs:**

| File | Purpose |
|------|---------|
| `audit/onet_task_text_duplicates.csv` | All O\*NET tasks shared across SOCs |
| `audit/anthropic_tasks_ambiguous_matches.csv` | Anthropic tasks with ambiguous mappings |
| `audit/exposure_accounting_check.csv` | Verify usage totals are conserved |

**Methods section language:**

> "Because O\*NET task statements can be shared across multiple occupations, a subset of Anthropic task strings maps to multiple SOCs. We treat these mappings as ambiguous and allocate usage across candidate occupations using a conservative equal-split rule. We report employment-weighted allocation as a robustness check."

### 2.6 Step 5: O\*NET Attribute Enrichment

For each matched task, retrieve standard O\*NET attributes:

#### 4a. Occupation Attributes

| Attribute | Source File | Join Key |
|-----------|-------------|----------|
| Occupation title | `Occupation Data.txt` | `O*NET-SOC Code` |
| Occupation description | `Occupation Data.txt` | `O*NET-SOC Code` |
| Job Zone (1-5) | `Job Zones.txt` | `O*NET-SOC Code` |
| Typical education | `Education, Training, and Experience.txt` | `O*NET-SOC Code` |

#### 4b. Task Ratings

| Rating | Scale ID | Description | Source |
|--------|----------|-------------|--------|
| Task Importance | IM | How important is this task? (1-5) | `Task Ratings.txt` |
| Task Relevance | RT | % of incumbents saying task is part of job | `Task Ratings.txt` |

```python
# Extract task ratings
task_ratings = ratings[ratings['Scale ID'].isin(['IM', 'RT'])]
importance = task_ratings[task_ratings['Scale ID'] == 'IM']
relevance = task_ratings[task_ratings['Scale ID'] == 'RT']
```

**Why task ratings matter:** Task importance and relevance are standard weights in labor economics. They indicate how central a task is to an occupation (Autor, Levy & Murnane 2003).

#### 4c. Detailed Work Activities (DWAs)

| File | Purpose |
|------|---------|
| `Tasks to DWAs.txt` | Maps each task to related DWAs |
| `DWA Reference.txt` | DWA titles and descriptions |
| `IWA Reference.txt` | Intermediate Work Activity groupings |

**Why DWAs:** DWAs are standardized, generalizable work activities that allow comparison across occupations. Used by Eloundou et al. (2023) for GPT exposure analysis.

#### 4d. Non-Routine Task Classification

**Literature basis:** Autor, Levy & Murnane (2003), Acemoglu & Autor (2011), Autor & Dorn (2013)

**Method:** Use O\*NET Work Activities scores to classify task content.

| Measure | O\*NET Element IDs | Interpretation |
|---------|-------------------|----------------|
| Non-routine cognitive analytical | 4.A.2.a.4, 4.A.2.b.2 | Analyzing data, creative thinking |
| Non-routine cognitive interpersonal | 4.A.4.a.4, 4.A.4.b.4 | Interpersonal relationships, managing |
| Non-routine manual | 4.A.3.a.3 | Operating vehicles/equipment |

**Normalization:** Raw scores (1-5 or 1-7) normalized to 0-1 scale:
```python
normalized = (raw_score - min_score) / (max_score - min_score)
```

**Composite score:**
```python
nonroutine_total = (nonroutine_cognitive_analytical +
                    nonroutine_cognitive_interpersonal +
                    nonroutine_manual) / 3
```

**Interpretation:** Higher `nonroutine_total` = task is less routine = less automatable by traditional criteria. Note: LLMs may automate non-routine cognitive tasks, reversing traditional patterns.

### 2.6 Step 5: BLS Wage Linkage

**Join method:** 6-digit SOC code

```python
# O*NET uses 8-digit codes: 15-1252.00
# BLS uses 6-digit codes: 15-1252
crosswalk['soc_6digit'] = crosswalk['onet_soc_code'].str.split('.').str[0]

# Merge
merged = crosswalk.merge(
    bls_wages,
    left_on='soc_6digit',
    right_on='OCC_CODE',
    how='left'
)
```

**Result:** 2,046 tasks matched (96.9%), 65 unmatched

**Why some tasks unmatched:** O\*NET has more detailed occupation codes than BLS publishes separately. For example:
- O\*NET `29-2011.01` (Cytotechnologists)
- O\*NET `29-2011.02` (Histotechnologists)
- BLS aggregates both under `29-2011`

These 20 specialty SOC codes account for 65 unmatched task rows (3.1% of tasks, 2.2% of API usage).

---

## 3. Alignment with Academic Literature

### 3.1 Standard O\*NET Usage in Labor Economics

This crosswalk follows conventions established in the labor economics literature:

| Convention | Our Implementation | Canonical Reference |
|------------|-------------------|---------------------|
| SOC code as primary identifier | ✓ Full O\*NET-SOC codes retained | All O\*NET studies |
| Task-level analysis | ✓ Individual task statements | Autor, Levy & Murnane (2003) |
| Task importance weighting | ✓ IM scale from Task Ratings | Autor, Levy & Murnane (2003) |
| Task relevance/prevalence | ✓ RT scale from Task Ratings | Standard O\*NET practice |
| DWA mapping for generalizability | ✓ Detailed Work Activities | Eloundou et al. (2023) |
| Routine/non-routine classification | ✓ Work Activities elements | Autor & Dorn (2013) |
| BLS wage linkage | ✓ OEWS by SOC code | Standard in wage analysis |

### 3.2 Comparability with Existing AI Exposure Studies

| Study | Their Approach | Our Approach | Compatibility |
|-------|---------------|--------------|---------------|
| **Autor, Levy & Murnane (2003)** | O\*NET task content → routine/non-routine | Same element IDs and methodology | **Fully compatible** |
| **Autor & Dorn (2013)** | RTI index from work activities | Non-routine scores from same elements | **Fully compatible** |
| **Webb (2020)** | Patent text → O\*NET tasks | API usage → O\*NET tasks | **Directly comparable** |
| **Felten et al. (2021)** | AI capabilities → O\*NET abilities | Different level (tasks vs abilities) | Requires aggregation to abilities |
| **Eloundou et al. (2023)** | GPT annotations of O\*NET tasks/DWAs | Revealed usage vs hypothetical exposure | **Complementary** - can compare predicted vs actual |

### 3.3 Key Methodological Differences from Prior Work

| Aspect | Prior Studies | This Dataset |
|--------|--------------|--------------|
| **AI measure** | Hypothetical exposure (model predictions) | Revealed usage (actual API calls) |
| **Task source** | Full O\*NET task inventory | Tasks actually used via API |
| **Weighting** | Equal weight or task importance | API usage counts available |
| **Temporal** | Cross-sectional | Single week (Nov 2025) |
| **Product scope** | "AI" broadly | Claude API specifically |

---

## 4. Final Dataset Specification

### 4.1 Primary Output File

**File:** `processed/master_task_crosswalk_with_wages.csv`

| Metric | Value |
|--------|-------|
| Rows | 2,111 |
| Columns | 38 |
| O\*NET match rate | 93.8% (of Anthropic tasks) |
| BLS wage match rate | 96.9% (of matched tasks) |
| API usage coverage | 97.8% (of total API calls) |
| Unique occupations | 488 |

### 4.2 Match Quality Summary

| Match Type | Count | % of Matched | Quality |
|------------|-------|--------------|---------|
| Exact | 1,998 | 94.6% | Perfect text match after normalization |
| Fuzzy (≥85) | 113 | 5.4% | High-confidence semantic match |

### 4.3 Complete Variable Codebook

#### Anthropic Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `anthropic_task_description` | string | Original task text from API | Anthropic HuggingFace | 100% |
| `api_usage_count_original` | float | Original API call count before splitting | Anthropic HuggingFace | 100% |
| `api_usage_count` | float | API calls after equal-split allocation | Constructed | 100% |

#### Ambiguous Task Handling Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `split_weight` | float | Weight applied (1/N for N candidate SOCs) | Constructed | 100% |
| `n_candidate_socs` | integer | Number of SOCs this task maps to | Constructed | 100% |
| `is_ambiguous` | boolean | True if task maps to multiple SOCs | Constructed | 100% |
| `ambiguous_group_id` | integer | Unique ID for auditing ambiguous groups | Constructed | For ambiguous only |

#### Matching Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `match_method` | string | "exact" or "fuzzy" | Constructed | 100% |
| `match_score` | float | 100 for exact, 85-99 for fuzzy | Constructed | 100% |

#### O\*NET Task Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `onet_soc_code` | string | O\*NET-SOC code (e.g., 15-1252.00) | Task Statements.txt | 100% |
| `onet_task_id` | integer | O\*NET task identifier | Task Statements.txt | 100% |
| `onet_task_description` | string | Official O\*NET task text | Task Statements.txt | 100% |
| `onet_task_type` | string | "Core" or "Supplemental" | Task Statements.txt | 94.8% |

#### O\*NET Occupation Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `onet_occupation_title` | string | Occupation name | Occupation Data.txt | 100% |
| `onet_occupation_description` | string | Full occupation description | Occupation Data.txt | 100% |
| `Job Zone` | integer | 1-5 education/preparation level | Job Zones.txt | 100% |
| `typical_education` | string | Most common education level | Education, Training...txt | 92.9% |
| `typical_education_pct` | float | % with typical education | Education, Training...txt | 92.9% |

#### O\*NET Task Rating Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `task_importance` | float | How important (1-5 scale) | Task Ratings.txt (IM) | 94.2% |
| `task_relevance` | float | % saying task is part of job | Task Ratings.txt (RT) | 94.2% |

#### O\*NET Work Activity Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `dwa_ids` | string | Detailed Work Activity IDs (semicolon-separated) | Tasks to DWAs.txt | 98.2% |
| `dwa_titles` | string | DWA descriptions (semicolon-separated) | DWA Reference.txt | 98.2% |
| `iwa_ids` | string | Intermediate Work Activity IDs | IWA Reference.txt | 98.2% |

#### Task Content Classification Variables

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `nonroutine_cognitive_analytical` | float | 0-1 score | Work Activities.txt | 96.1% |
| `nonroutine_cognitive_interpersonal` | float | 0-1 score | Work Activities.txt | 96.1% |
| `nonroutine_manual` | float | 0-1 score | Work Activities.txt | 96.1% |
| `nonroutine_total` | float | Average of above (0-1) | Constructed | 96.1% |

#### BLS Wage Variables (May 2024)

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| `soc_6digit` | string | 6-digit SOC for BLS join | Constructed | 100% |
| `OCC_CODE` | string | BLS occupation code | OEWS | 97.3% |
| `OCC_TITLE` | string | BLS occupation title | OEWS | 97.3% |
| `TOT_EMP` | integer | Total U.S. employment | OEWS | 97.3% |
| `H_MEAN` | float | Hourly mean wage ($) | OEWS | 93.5% |
| `A_MEAN` | float | Annual mean wage ($) | OEWS | 96.9% |
| `H_MEDIAN` | float | Hourly median wage ($) | OEWS | 92.6% |
| `A_MEDIAN` | float | Annual median wage ($) | OEWS | 96.0% |
| `H_PCT10` | float | Hourly 10th percentile ($) | OEWS | 93.5% |
| `H_PCT25` | float | Hourly 25th percentile ($) | OEWS | 93.5% |
| `H_PCT75` | float | Hourly 75th percentile ($) | OEWS | 92.1% |
| `H_PCT90` | float | Hourly 90th percentile ($) | OEWS | 87.2% |
| `A_PCT10` | float | Annual 10th percentile ($) | OEWS | 96.9% |
| `A_PCT25` | float | Annual 25th percentile ($) | OEWS | 96.9% |
| `A_PCT75` | float | Annual 75th percentile ($) | OEWS | 95.5% |
| `A_PCT90` | float | Annual 90th percentile ($) | OEWS | 90.5% |

### 4.4 Job Zone Definitions

| Zone | Name | Typical Education | Example Occupations |
|------|------|-------------------|---------------------|
| 1 | Little or No Preparation | Less than high school | Food prep, cashiers |
| 2 | Some Preparation | High school diploma | Customer service, clerks |
| 3 | Medium Preparation | Some college, vocational | Technicians, trades |
| 4 | Considerable Preparation | Bachelor's degree | Engineers, analysts |
| 5 | Extensive Preparation | Graduate degree | Scientists, physicians |

---

## 5. Limitations and Caveats

### 5.1 Data Limitations

| Limitation | Description | Implication |
|------------|-------------|-------------|
| **Single AI product** | Claude API only | Cannot generalize to all AI |
| **Selection bias** | Users who choose Claude | Not representative of all AI users |
| **Point-in-time** | One week (Nov 2025) | Cannot track trends |
| **API only** | Excludes Claude.ai consumer usage | Misses personal/consumer use |
| **U.S. wages only** | BLS covers U.S. workers | Cannot analyze global wage effects |

### 5.2 Methodological Limitations

| Limitation | Description | Implication |
|------------|-------------|-------------|
| **Task ≠ automation** | Using AI for a task ≠ replacing workers | Cannot infer job loss |
| **No causal ID** | Cross-sectional data | Cannot identify causal effects |
| **Unmatched tasks** | 6.2% of tasks (3.2% of usage) unmatched | Some usage not in analysis |
| **Classifier accuracy** | Anthropic's O\*NET classifier unknown | Task assignments may have errors |

### 5.3 Unmatched Tasks

**142 Anthropic task descriptions could not be matched to O\*NET:**

| Reason | Likely Explanation |
|--------|-------------------|
| Anthropic-specific tasks | Tasks not in O\*NET taxonomy |
| Classifier errors | Anthropic's classifier may have misclassified |
| Text variations | Differences too large for fuzzy matching |

**Saved to:** `processed/unmatched_tasks.csv` for review

---

## 6. File Structure

```
anthropic-onet-crosswalk/
├── README.md                              # This documentation
├── THEORETICAL_FRAMEWORK.md               # Economic theory guide
│
├── data/
│   ├── raw/
│   │   ├── onet_db.zip                   # Original O*NET download
│   │   └── db_29_1_text/                 # Extracted O*NET files (41 files)
│   │
│   ├── processed/
│   │   ├── master_task_crosswalk_with_wages.csv  # PRIMARY OUTPUT
│   │   ├── master_task_crosswalk.csv             # Without BLS wages
│   │   └── unmatched_tasks.csv                   # Failed matches
│   │
│   ├── audit/                            # Audit trail for transparency
│   │   ├── onet_task_text_duplicates.csv         # O*NET tasks in multiple SOCs
│   │   ├── anthropic_tasks_ambiguous_matches.csv # Ambiguous Anthropic→SOC mappings
│   │   └── exposure_accounting_check.csv         # Usage conservation verification
│   │
│   ├── analysis/
│   │   ├── occupation_ai_exposure_equal.csv      # MAIN: Equal-split exposure
│   │   ├── occupation_ai_exposure_empweighted.csv # Robustness: Emp-weighted
│   │   ├── model_summary.csv                     # Model results (both specs)
│   │   └── sensitivity_equal_vs_empweighted.csv  # Sensitivity comparison
│   │
│   └── BLS/
│       └── oesm24all/                    # May 2024 OEWS wage data
│
└── scripts/
    ├── python/
    │   ├── build_crosswalk.py            # Build crosswalk (pandas, rapidfuzz)
    │   └── estimate_models.py            # Estimate models (pandas, numpy)
    │
    └── R/
        ├── build_crosswalk.R             # Build crosswalk (tidyverse, stringdist)
        └── estimate_models.R             # Estimate models (tidyverse)
```

---

## 7. Reproducibility

### 7.1 Requirements

```
Python 3.8+
pandas
rapidfuzz
openpyxl
```

### 7.2 Rebuild Instructions

```bash
# Install dependencies
pip install pandas rapidfuzz openpyxl

# Run build script
cd scripts
python build_crosswalk.py

# Run theoretical models
python estimate_models.py
```

### 7.3 Data Downloads

| Data | URL | Action |
|------|-----|--------|
| Anthropic | https://huggingface.co/datasets/Anthropic/EconomicIndex | Download CSV |
| O\*NET | https://www.onetcenter.org/database.html | Download db_29_1_text.zip |
| BLS OEWS | https://www.bls.gov/oes/tables.htm | Download oesm24all.zip |

---

## 8. Linking to Additional Data

This crosswalk enables linkage to many external datasets via SOC code:

### 8.1 Already Linked

| Dataset | Status | Join Key |
|---------|--------|----------|
| BLS OEWS wages | ✓ Included | `soc_6digit` = `OCC_CODE` |

### 8.2 Can Be Linked

| Dataset | Join Key | Variables Available |
|---------|----------|---------------------|
| BLS Employment Projections | 6-digit SOC | 10-year growth, separations |
| Census/ACS | SOC (with crosswalk) | Demographics, income |
| Webb (2020) AI exposure | SOC | Patent-based AI exposure |
| Felten et al. (2021) AIOE | SOC | Ability-based AI exposure |
| Eloundou et al. (2023) | O\*NET task/DWA | GPT exposure scores |

---

## 9. Citation

### 9.1 Citing This Dataset

```bibtex
@misc{strauss2026crosswalk,
  author = {Strauss, Ilan},
  title = {Anthropic API Task to O*NET-BLS Crosswalk Dataset},
  year = {2026},
  publisher = {AI Disclosures Project},
  url = {https://github.com/IlanStrauss/anthropic-onet-crosswalk}
}
```

### 9.2 Citing Data Sources

```bibtex
@misc{anthropic2026economic,
  author = {{Anthropic}},
  title = {Anthropic Economic Index},
  year = {2026},
  url = {https://huggingface.co/datasets/Anthropic/EconomicIndex}
}

@misc{onet2024database,
  author = {{National Center for O*NET Development}},
  title = {O*NET Database, Version 29.1},
  year = {2024},
  url = {https://www.onetcenter.org/database.html}
}

@misc{bls2024oews,
  author = {{U.S. Bureau of Labor Statistics}},
  title = {Occupational Employment and Wage Statistics, May 2024},
  year = {2024},
  url = {https://www.bls.gov/oes/}
}
```

---

## 10. References

### Foundational Task-Based Labor Economics

- Autor, D., Levy, F. & Murnane, R. (2003). The skill content of recent technological change: An empirical exploration. *Quarterly Journal of Economics*, 118(4), 1279-1333.

- Acemoglu, D. & Autor, D. (2011). Skills, tasks and technologies: Implications for employment and earnings. *Handbook of Labor Economics*, 4, 1043-1171.

- Autor, D. & Dorn, D. (2013). The growth of low-skill service jobs and the polarization of the US labor market. *American Economic Review*, 103(5), 1553-1597.

### AI and Automation

- Acemoglu, D. & Restrepo, P. (2018). The race between man and machine: Implications of technology for growth, factor shares, and employment. *American Economic Review*, 108(6), 1488-1542.

- Acemoglu, D. & Restrepo, P. (2019). Automation and new tasks: How technology displaces and reinstates labor. *Journal of Economic Perspectives*, 33(2), 3-30.

### AI Exposure Indices

- Webb, M. (2020). The impact of artificial intelligence on the labor market. *Stanford Working Paper*.

- Felten, E., Raj, M. & Seamans, R. (2021). Occupational, industry, and geographic exposure to artificial intelligence: A novel dataset and its potential uses. *Strategic Management Journal*, 42(12), 2195-2217.

- Eloundou, T., Manning, S., Mishkin, P. & Rock, D. (2023). GPTs are GPTs: An early look at the labor market impact potential of large language models. *arXiv preprint*.

### Post-Keynesian / Kaleckian Models

- Kalecki, M. (1954). *Theory of Economic Dynamics*. London: Allen & Unwin.

- Kalecki, M. (1971). *Selected Essays on the Dynamics of the Capitalist Economy*. Cambridge University Press.

- Bhaduri, A. & Marglin, S. (1990). Unemployment and the real wage: The economic basis for contesting political ideologies. *Cambridge Journal of Economics*, 14(4), 375-393.

- Stockhammer, E. & Stehrer, R. (2011). Goodwin or Kalecki in demand? Functional income distribution and aggregate demand in the short run. *Review of Radical Political Economics*, 43(4), 506-522.

- Onaran, Ö. & Galanis, G. (2014). Income distribution and growth: A global model. *Environment and Planning A*, 46(10), 2489-2513.

- Lavoie, M. & Stockhammer, E. (2013). Wage-led growth: Concept, theories and policies. In *Wage-Led Growth* (pp. 13-39). Palgrave Macmillan.

---

*Last updated: January 2026*
