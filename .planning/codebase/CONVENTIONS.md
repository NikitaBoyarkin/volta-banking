# Coding Conventions

**Analysis Date:** 2026-05-01

## Naming Patterns

**Files:**
- `volta_{analysis_type}.py` for analysis scripts
- `utils/{module}.py` for utility modules
- `viz{N}_{description}.png` for generated charts

**Functions:**
- `snake_case` for all functions
- Descriptive names: `calc_sample_size`, `generate_excel_report`, `extract_tables_from_pdf`
- Private helpers prefixed with underscore: `_create_summary_sheet`, `_add_sheet`

**Variables:**
- `snake_case` for variables
- DataFrames named `df`, `cohort_df`, `summary_stats`
- No special constant naming (color constants in `report_generator.py` use `COLOR_RED` UPPER_SNAKE_CASE)

**Types:**
- No type hints in analysis scripts
- Utility modules (`utils/`) use type hints in function signatures: `List[str]`, `Optional[Union[pd.DataFrame, str]]`
- Docstrings use Google/NumPy style (Parameters, Returns, Examples)

## Code Style

**Formatting:**
- No configured formatter or linter
- Manual indentation: 4 spaces
- Line length: Not enforced, some lines exceed 100 characters

**Linting:**
- None configured
- No CI checks

## Import Organization

**Order:**
1. Standard library (`os`, `warnings`, `datetime`)
2. Third-party packages (`pandas`, `numpy`, `matplotlib`)
3. Internal modules (`from utils.report_generator import ...`)

**Grouping:**
- No blank lines between import groups consistently
- Some scripts group by purpose with comment headers

**Path Aliases:**
- None

## Error Handling

**Patterns:**
- No try/except blocks in analysis scripts
- `warnings.filterwarnings('ignore')` at top of each script
- Utility functions return empty DataFrames on failure rather than raising

**Error Types:**
- No custom error classes
- Fail-fast on missing CSV files (`FileNotFoundError`)

## Logging

**Framework:**
- `print()` statements only
- No structured logging

**Patterns:**
- `print('=' * 70)` for section headers
- `print(f'✓ Saved to {path}')` for success messages in utilities
- Progress printed to stdout in real-time

## Comments

**When to Comment:**
- Section headers with `===` banners: `# === SECTION 1: Setup ===`
- Metric definitions in docstrings
- Business context in module-level docstrings (extensive)

**TODO Comments:**
- Placeholder functions marked with `# TODO: Implement ...`
- `report_generator.py`: `# TODO: Implement PDF generation using reportlab`

## Function Design

**Size:**
- Analysis scripts have large monolithic blocks
- Utility functions are modular and well-scoped (20-50 lines)
- Some analysis functions exceed 100 lines

**Parameters:**
- Prefer positional args with defaults
- Object-style parameters in utilities: `generate_excel_report(data_dict, output_path, title="...", author="...")`

**Return Values:**
- Utility functions return paths or DataFrames
- Print side effects common in analysis scripts

## Module Design

**Exports:**
- `utils/__init__.py` explicitly exports all public functions
- Analysis scripts have no exports (run as scripts)

**Barrel Files:**
- `utils/__init__.py` acts as barrel for report generator and PDF processor

---

*Convention analysis: 2026-05-01*
*Update when patterns change*
