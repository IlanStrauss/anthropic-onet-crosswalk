# Data Sources and Construction

This document explains where all datasets come from and how they were constructed.

---

## **Primary Datasets**

### **1. Master Task Crosswalk (with Importance Weights)**
**File:** `processed/master_task_crosswalk_with_importance.csv`

**Description:** Links Anthropic Claude API task descriptions to O*NET SOC occupations, with BLS wage/employment data and O*NET task importance weights.

**Sources:**
- **Anthropic Claude API task data**: Internal usage data (anthropic_task_description, api_usage_count)
- **O*NET Task Statements**: https://www.onetcenter.org/database.html
  - File: `Task Statements.xlsx`
  - Provides: O*NET-SOC codes, task IDs, task descriptions
- **O*NET Task Ratings (Importance)**: https://www.onetcenter.org/database.html
  - File: `Task Ratings.xlsx`
  - Provides: Task importance weights (Scale ID = 'IM', values 0-5)
  - Version: O*NET 30.1 Database (December 2024 release)
- **BLS OES Wage Data**: https://www.bls.gov/oes/tables.htm
  - Year: May 2024
  - Provides: TOT_EMP, A_MEAN, A_MEDIAN, H_MEAN, job_zone, typical_education

**Construction Method:**
1. **Semantic matching** (via embedding similarity) between Anthropic task descriptions and O*NET task descriptions
2. **Human validation** of ambiguous matches (flagged with `is_ambiguous=True`)
3. **Split-weight allocation** for tasks mapping to multiple SOC codes
4. **O*NET-BLS merge** on O*NET-SOC code → 6-digit SOC code
5. **Task importance merge** on (O*NET-SOC Code, Task ID) pairs

**Key Columns:**
- `anthropic_task_description`: Claude API task description
- `api_usage_count`: Number of Claude API calls for this task (split-weighted if ambiguous)
- `api_usage_count_original`: Original count before split-weighting
- `onet_soc_code`: O*NET-SOC occupation code (e.g., "15-1252.00")
- `onet_task_id`: O*NET task ID
- `onet_task_description`: O*NET canonical task description
- `task_importance`: O*NET importance rating (0-5 scale, higher = more important)
- `soc_6digit`: BLS 6-digit SOC code (e.g., "15-1252")
- `TOT_EMP`: Total employment in occupation
- `A_MEAN`: Annual mean wage
- `job_zone`: O*NET Job Zone (1-5, complexity/education level)
- `match_score`: Semantic similarity score (0-1)
- `is_ambiguous`: Boolean flag for human-validated ambiguous mappings

**Row Interpretation:**
- Each row = one (Anthropic task, O*NET task, SOC occupation) tuple
- For unambiguous mappings: one Anthropic task → one O*NET task → one SOC
- For ambiguous mappings: one Anthropic task → multiple O*NET tasks → multiple SOCs (with split weights)

---

### **2. Wage Panel (2022-2024)**
**File:** `processed/wage_panel_2022_2024.csv`

**Description:** Panel dataset of occupation-level wages and employment across three years, enabling empirical validation of theoretical models.

**Source:**
- **BLS OES National Estimates**: https://www.bls.gov/oes/tables.htm
  - May 2022: `national_M2022_dl.xlsx`
  - May 2023: `national_M2023_dl.xlsx`
  - May 2024: `national_M2024_dl.xlsx`
  - Geographic scope: U.S. National, cross-industry
  - Released: Annually each March/April

**Construction Method:**
1. Downloaded BLS OES national cross-industry estimates for 2022-2024
2. Filtered to: AREA=99 (National), NAICS=0 (Cross-industry)
3. Excluded aggregate row (OCC_CODE='00-0000')
4. Converted wage/employment columns to numeric (handles suppressed "#" values)
5. Dropped rows with missing wages or employment
6. Stacked into long-format panel with year indicator

**Key Columns:**
- `soc_code`: BLS 6-digit SOC code
- `occ_title`: Occupation title
- `year`: Survey year (2022, 2023, 2024)
- `employment`: Total employment (TOT_EMP)
- `wage_annual_mean`: Annual mean wage (A_MEAN)
- `wage_annual_median`: Annual median wage (A_MEDIAN)
- `wage_hourly_mean`: Hourly mean wage (H_MEAN)

**Use Cases:**
- Compute wage growth: Δln(w) = ln(wage_2024) - ln(wage_2022)
- Test Acemoglu-Restrepo predictions: Does AI exposure predict wage changes?
- Control for occupation-level trends in theoretical models

**CRITICAL TIMING NOTE:**
- ChatGPT/GPT-4 released March 2023, Claude released March 2023
- **2022 baseline predates LLM availability**
- 2022-2024 growth tests if AI exposure proxies for pre-existing task vulnerability
- 2023-2024 growth isolates post-LLM period
- See `models/acemoglu_restrepo/empirical_validation.py` for timing robustness checks

**Finding:** Effect is present in BOTH periods (β ≈ -0.06***), suggesting AI exposure measures task characteristics that made occupations vulnerable BEFORE LLMs, not causal LLM impact.

---

## **Supporting Data (Raw)**

### **O*NET Database**
**Directory:** `onet/db_30_1_excel/`

**Source:** https://www.onetcenter.org/database.html
**Version:** O*NET 30.1 Database (December 2024 release)
**Format:** Microsoft Excel (40 files)

**Key Files Used:**
- `Task Statements.xlsx`: Task descriptions by occupation
- `Task Ratings.xlsx`: Task importance, frequency, relevance ratings
- Other files available but not currently used (Skills, Abilities, Work Activities, etc.)

**Download Command:**
```bash
curl -O https://www.onetcenter.org/dl_files/database/db_30_1_excel.zip
unzip db_30_1_excel.zip -d data/onet/
```

---

### **BLS OES Historical Data**
**Directory:** `bls_oes/`

**Source:** https://www.bls.gov/oes/tables.htm

**Files:**
- `national_M2022_dl.xlsx`: May 2022 national estimates
- `national_M2023_dl.xlsx`: May 2023 national estimates
- `national_M2024_dl.xlsx`: May 2024 national estimates

**Download:**
- Manual download from BLS website (requires browser, blocks direct curl)
- Or use Playwright MCP browser automation

**Note:** Historical data goes back to 1997, but only 2022-2024 currently used.

---

## **Data Processing Scripts**

### **1. Add Task Importance and Build Wage Panel**
**Script:** `scripts/add_task_importance_and_wage_panel.py`

**Inputs:**
- `processed/master_task_crosswalk_with_wages.csv`
- `onet/db_30_1_excel/Task Ratings.xlsx`
- `bls_oes/national_M20{22,23,24}_dl.xlsx`

**Outputs:**
- `processed/master_task_crosswalk_with_importance.csv` (adds task_importance column)
- `processed/wage_panel_2022_2024.csv` (panel dataset)

**Run:**
```bash
python3 data/scripts/add_task_importance_and_wage_panel.py
```

---

## **Data Quality Notes**

### **Task Importance Merge (95.4% Match Rate)**
- 2,532 / 2,653 rows matched to O*NET importance ratings
- 121 unmatched rows filled with mean importance (4.0)
- Unmatched tasks likely due to:
  - O*NET database updates between versions
  - Task ID mismatches
  - Non-standard task descriptions

### **BLS Wage Suppression**
- Some wages marked "#" (suppressed for data quality/confidentiality)
- Dropped ~7 occupations per year with missing wages
- Total: 1,394-1,395 occupations per year (out of 1,401-1,402 total)

### **SOC Code Mapping**
- O*NET uses 8-digit SOC (e.g., "15-1252.00")
- BLS OES uses 6-digit SOC (e.g., "15-1252")
- Crosswalk merges on truncated 6-digit codes
- Some detail lost when O*NET subdivides BLS occupations

---

## **Data Versioning**

| Dataset | Version | Release Date | Download Date |
|---------|---------|--------------|---------------|
| O*NET Database | 30.1 | December 2024 | January 2026 |
| BLS OES (2024) | May 2024 | March 2025 | January 2026 |
| BLS OES (2023) | May 2023 | March 2024 | January 2026 |
| BLS OES (2022) | May 2022 | March 2023 | January 2026 |
| Anthropic Task Data | Internal | - | January 2026 |

---

## **Citation**

If using this data, cite:

**O*NET:**
> National Center for O*NET Development. (2024). O*NET 30.1 Database. U.S. Department of Labor/Employment and Training Administration. https://www.onetcenter.org/

**BLS OES:**
> U.S. Bureau of Labor Statistics. (2024). Occupational Employment and Wage Statistics. https://www.bls.gov/oes/

**This Project:**
> Strauss, I. (2026). Anthropic O*NET Task Crosswalk with AI Exposure Measures. AI Disclosures Project.

---

## **Contact**

For questions about data construction or access:
- GitHub Issues: https://github.com/IlanStrauss/anthropic-onet-crosswalk/issues
- See main repository README for contact information
