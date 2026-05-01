# Architecture

**Analysis Date:** 2026-05-01

## Pattern Overview

**Overall:** Standalone Analytical Scripts (Notebook-style)

**Key Characteristics:**
- Four self-contained, sequential analysis scripts
- No shared runtime or application state
- Each script is independently executable
- Script-at-a-time execution (not a service or app)
- Data flows from CSV → pandas → matplotlib → output files

## Layers

**Data Loading Layer:**
- Purpose: Read CSV files into pandas DataFrames
- Contains: `pd.read_csv()` calls with relative paths
- Depends on: Local filesystem, CSV files in repo root or `data/`
- Used by: Analysis layer in each script

**Analysis Layer:**
- Purpose: Statistical computations, segmentation, hypothesis testing
- Contains: Custom functions for sample size calculation, bootstrap intervals, K-means clustering, cohort retention math
- Depends on: Data Loading layer, numpy, scipy, scikit-learn
- Used by: Visualization layer

**Visualization Layer:**
- Purpose: Generate charts and plots
- Contains: `matplotlib.pyplot` and `seaborn` calls
- Depends on: Analysis layer outputs
- Used by: Output layer (saves to PNG)

**Utility Layer:**
- Purpose: Reusable report generation and PDF processing
- Contains: `utils/report_generator.py`, `utils/pdf_processor.py`
- Depends on: pandas, openpyxl, pdfplumber, pypdf
- Used by: Not currently used by main analysis scripts (intended for future report automation)

## Data Flow

**Script Execution Lifecycle:**

1. User runs: `uv run python volta_funnel_analysis.py`
2. Script loads CSV via relative path: `pd.read_csv('volta_funnel_data.csv')`
3. Data quality checks and preprocessing
4. Statistical computations (conversion rates, Chi-square tests)
5. Visualization generation (matplotlib charts)
6. Charts saved to PNG files via `plt.savefig()`
7. Optional: Excel report generation via `utils/report_generator.py`
8. Results printed to stdout

**State Management:**
- Stateless — Each execution is independent
- No persistent state between runs
- Data loaded fresh from CSV each time

## Key Abstractions

**Analysis Script:**
- Purpose: Self-contained end-to-end analysis for one business question
- Examples: `volta_funnel_analysis.py`, `volta_ab_testing.py`, `volta_retention_analysis.py`, `volta_segmentation.py`
- Pattern: Import → Load CSV → Analyze → Visualize → Output

**Report Generator:**
- Purpose: Excel report automation with professional formatting
- Examples: `utils/report_generator.py` — `generate_excel_report()`, `generate_funnel_excel()`, `generate_ab_test_excel()`
- Pattern: Function accepts `data_dict` of DataFrames, produces multi-sheet `.xlsx`

**PDF Processor:**
- Purpose: Extract structured data from PDFs (bank statements, reports)
- Examples: `utils/pdf_processor.py` — `extract_tables_from_pdf()`, `parse_bank_statement()`
- Pattern: Function accepts PDF path, returns DataFrames or dictionaries

## Entry Points

**CLI Entry:**
- Location: Each `volta_*.py` file is independently executable
- Triggers: `uv run python volta_funnel_analysis.py` (or any of the 4 scripts)
- Responsibilities: Load data, run analysis, print results, save charts

**Stub Entry:**
- Location: `main.py`
- Triggers: `uv run python main.py`
- Responsibilities: Prints "Hello from volta-banking!" — not the actual entry point

## Error Handling

**Strategy:** No centralized error handling; scripts use standard Python exceptions

**Patterns:**
- `warnings.filterwarnings('ignore')` at top of each script to suppress noisy library warnings
- CSV loading assumes files exist in repo root; `FileNotFoundError` if run from wrong directory
- No try/catch around data loading — fails fast

## Cross-Cutting Concerns

**Logging:**
- `print()` statements for progress indication
- No structured logging framework

**Visualization Style:**
- `plt.style.use('dark_background')` in every script
- Consistent color scheme across all analyses

**Path Conventions:**
- Relative paths assumed from repo root
- Some scripts load from root (`volta_funnel_data.csv`), others from `data/` (`data/volta_funnel_data.csv`)
- Inconsistent path conventions between scripts

---

*Architecture analysis: 2026-05-01*
*Update when major patterns change*
