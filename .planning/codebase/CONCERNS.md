# Codebase Concerns

**Analysis Date:** 2026-05-01

## Tech Debt

**Inconsistent CSV path conventions:**
- Issue: Scripts load CSVs from different locations — some from repo root (`volta_funnel_data.csv`), others from `data/` (`data/volta_funnel_data.csv`)
- Files: `volta_funnel_analysis.py` (root), other scripts vary
- Why: Scripts evolved independently without standardization
- Impact: Scripts break if moved or if data files are reorganized
- Fix approach: Standardize all paths to `data/` prefix, add path resolution utility

**Placeholder utility functions:**
- Issue: `generate_pdf_summary()` and `generate_word_report()` in `utils/report_generator.py` are unimplemented stubs
- Files: `utils/report_generator.py` (lines 302-369)
- Why: Planned features not yet built
- Impact: Calling these functions prints warnings but does nothing useful
- Fix approach: Implement with `reportlab`/`python-docx` or remove stubs

**No virtual environment in .gitignore:**
- Issue: `.venv/` is not explicitly gitignored
- Why: `.gitignore` may not exist or may not include `.venv/`
- Impact: Risk of accidentally committing virtual environment files
- Fix approach: Add `.venv/` to `.gitignore`

## Known Bugs

**Scripts fail when run outside repo root:**
- Symptoms: `FileNotFoundError` for CSV files
- Trigger: Running script from any directory other than repo root
- Files: All `volta_*.py` scripts
- Workaround: Always `cd` to repo root before running
- Root cause: Hardcoded relative paths like `pd.read_csv('volta_funnel_data.csv')`
- Fix: Use `Path(__file__).parent` or similar for path resolution

## Security Considerations

**No secrets in codebase:**
- Risk: Low — This is an offline analytics portfolio with no external services
- Current mitigation: No API keys, no credentials, no environment variables with secrets
- Recommendations: N/A for current scope; if RAG tool is built per `doc/PRD_RAG_Documentation.md`, implement proper secret management

## Performance Bottlenecks

**Data loading:**
- Problem: CSVs are loaded into memory each script run with no caching
- Measurement: ~1-2 seconds for 10k-row datasets (negligible)
- Cause: `pd.read_csv()` called fresh each execution
- Improvement path: Not needed at current data sizes; consider parquet for larger datasets

**Visualization generation:**
- Problem: Matplotlib charts saved as high-resolution PNGs
- Measurement: Acceptable for current dataset sizes
- Cause: `plt.savefig()` with default DPI
- Improvement path: Not needed currently

## Fragile Areas

**Hardcoded business parameters:**
- Files: All `volta_*.py` scripts
- Why fragile: Business assumptions (LTV values, pricing, MDE) are inline constants
- Common failures: If business context changes, constants must be updated in multiple files
- Safe modification: Extract constants to a shared config module
- Test coverage: None

**K-means random state:**
- File: `volta_segmentation.py`
- Why fragile: Clustering results may vary between runs if `random_state` not fixed
- Common failures: Reproducibility issues
- Safe modification: Ensure `random_state` is explicitly set in `KMeans()`
- Test coverage: None

## Scaling Limits

**Single-machine execution:**
- Current capacity: Handles 10k-row datasets easily
- Limit: Memory-bound by pandas (millions of rows)
- Symptoms at limit: Memory exhaustion, slow processing
- Scaling path: Use Dask/polars for larger datasets, or sample data

**Synthetic data only:**
- Current capacity: Educational/demonstrative workloads
- Limit: Not designed for production data volumes
- Symptoms at limit: Scripts are not optimized for performance
- Scaling path: Refactor with chunked processing, database connections

## Dependencies at Risk

**None identified** — All dependencies are actively maintained standard data science libraries.

## Missing Critical Features

**Test suite:**
- Problem: No automated tests for any analysis logic
- Current workaround: Manual verification by running scripts
- Blocks: Safe refactoring, regression detection, CI/CD
- Implementation complexity: Low (add pytest + basic assertions)

**Linting and formatting:**
- Problem: No code style enforcement
- Current workaround: Manual code review
- Blocks: Consistent code quality
- Implementation complexity: Low (add ruff/black to `pyproject.toml`)

**CI/CD pipeline:**
- Problem: No automated checks on commits
- Current workaround: None
- Blocks: Automated testing, deployment, quality gates
- Implementation complexity: Low (GitHub Actions workflow)

## Test Coverage Gaps

**All analysis logic:**
- What's not tested: Statistical calculations, visualization generation, data transformations
- Risk: Silent bugs in math or data processing
- Priority: Medium
- Difficulty to test: Low — synthetic data provides deterministic inputs

**Utility modules:**
- What's not tested: `utils/report_generator.py`, `utils/pdf_processor.py`
- Risk: Report generation bugs
- Priority: Low
- Difficulty to test: Low

---

*Concerns audit: 2026-05-01*
*Update as issues are fixed or new ones discovered*
