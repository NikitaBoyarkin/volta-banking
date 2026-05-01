# Technology Stack

**Analysis Date:** 2026-05-01

## Languages

**Primary:**
- Python 3.10+ — All application and analysis code

**Secondary:**
- Markdown — Documentation (`README.md`, `CLAUDE.md`, `doc/PRD_RAG_Documentation.md`)
- CSV — Data files (`data/*.csv`)

## Runtime

**Environment:**
- CPython 3.10+ (`.python-version` specifies 3.14.2, `pyproject.toml` requires `>=3.10`)
- No server runtime; scripts are executed directly via `python script.py`

**Package Manager:**
- `uv` (preferred) — `uv.lock` present and should be kept in sync with `pyproject.toml`
- `pip` fallback supported
- Virtual environment: `.venv/` present in repo root

## Frameworks

**Core:**
- None — Standalone scripts, no web framework or application structure

**Data Science:**
- `pandas` 2.3.3+ — Data manipulation and CSV I/O
- `numpy` 2.0.2+ — Numerical computations
- `scipy` 1.13.1+ — Statistical tests (Chi-square, t-test, norm)
- `scikit-learn` — Clustering (`KMeans`), scaling (`StandardScaler`), PCA (`PCA`)
- `matplotlib` 3.9.4+ — Visualization (scripts set `plt.style.use('dark_background')`)
- `seaborn` 0.13.2+ — Statistical visualization

**Report Generation:**
- `openpyxl` 3.1.0+ — Excel report generation with charts and formatting

**PDF Processing:**
- `pdfplumber` 0.10.0+ — Table/text extraction from PDFs
- `pypdf` 4.0.0+ — PDF merging, splitting, metadata reading

**Development:**
- `ipykernel` 6.31.0+ — Jupyter kernel support (used in `.ipynb` notebooks)

## Key Dependencies

**Critical:**
- `pandas` 2.3.3+ — Core data structure for all analyses
- `numpy` 2.0.2+ — Underlying numerical operations
- `matplotlib` 3.9.4+ — All visualizations
- `scipy` 1.13.1+ — Statistical significance testing

**Infrastructure:**
- `openpyxl` 3.1.0+ — Excel output for report automation
- `pdfplumber` + `pypdf` — PDF processing utilities

## Configuration

**Environment:**
- No environment variables required
- No `.env` files
- Configuration is inline in scripts (e.g., `plt.style.use('dark_background')`, hardcoded paths)

**Build:**
- `pyproject.toml` — Project manifest and dependency list
- `uv.lock` — Pinned dependency lockfile
- No build step; scripts run directly

## Platform Requirements

**Development:**
- macOS/Linux/Windows with Python 3.10+
- `uv` recommended for dependency management
- CSV data files must be present in repo root or `data/` directory

**Production:**
- Not deployed; local execution only
- Each script must be run from repository root due to relative CSV paths

---

*Stack analysis: 2026-05-01*
*Update after major dependency changes*
