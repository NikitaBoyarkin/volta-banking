# Codebase Structure

**Analysis Date:** 2026-05-01

## Directory Layout

```
volta-banking/
├── data/                    # Input datasets (CSV)
├── doc/                     # Documentation and PRDs
│   └── PRD_RAG_Documentation.md
├── presentations/           # Slide decks (.pptx, .pdf)
├── utils/                   # Reusable utility modules
│   ├── __init__.py
│   ├── pdf_processor.py
│   └── report_generator.py
├── .venv/                   # Python virtual environment
├── CLAUDE.md                # Claude Code instructions
├── README.md                # Project documentation
├── main.py                  # Stub entry point
├── pyproject.toml           # Project manifest and dependencies
├── requirements.txt         # Pip-compatible requirements (empty)
├── uv.lock                  # uv dependency lockfile
├── volta_ab_testing.py      # Project 2/4: A/B Test Analysis
├── volta_funnel_analysis.py # Project 1/4: Onboarding Funnel
├── volta_retention_analysis.py # Project 3/4: Retention & Cohorts
├── volta_segmentation.py    # Project 4/4: User Segmentation
└── viz*.png                 # Generated visualizations
```

## Directory Purposes

**data/**
- Purpose: Input datasets for analyses
- Contains: Synthetic CSV files
- Key files: `volta_funnel_data.csv` (10k rows, user-level funnel data)
- Subdirectories: None

**doc/**
- Purpose: Documentation and product requirements
- Contains: `PRD_RAG_Documentation.md` (spec for a speculative internal RAG tool)
- Key files: `volta_doklad.docx`, `volta_doklad.pdf` (report artifacts in Russian)
- Subdirectories: None

**presentations/**
- Purpose: Slide decks for portfolio presentation
- Contains: `.pptx` and `.pdf` versions of portfolio slides
- Subdirectories: None

**utils/**
- Purpose: Reusable utility modules for report generation and PDF processing
- Contains: `report_generator.py`, `pdf_processor.py`
- Key files:
  - `report_generator.py` — Excel report generation with openpyxl
  - `pdf_processor.py` — PDF text/table extraction and manipulation
- Subdirectories: None

## Key File Locations

**Entry Points:**
- `volta_funnel_analysis.py` — Onboarding funnel analysis (Project 1/4)
- `volta_ab_testing.py` — A/B test analysis (Project 2/4)
- `volta_retention_analysis.py` — Cohort retention analysis (Project 3/4)
- `volta_segmentation.py` — User segmentation (Project 4/4)
- `main.py` — Stub (not the real entry point)

**Configuration:**
- `pyproject.toml` — Dependency list, Python version requirement
- `uv.lock` — Pinned dependency versions
- `.python-version` — Python version specifier

**Core Logic:**
- `volta_*.py` — The four analysis scripts
- `utils/report_generator.py` — Excel automation
- `utils/pdf_processor.py` — PDF processing utilities

**Testing:**
- None — No test files exist

**Documentation:**
- `README.md` — Project overview, business problem, key findings
- `CLAUDE.md` — Claude Code working instructions
- `doc/PRD_RAG_Documentation.md` — Spec for internal RAG documentation tool (in Russian)

## Naming Conventions

**Files:**
- `volta_{analysis_type}.py` — Analysis scripts (kebab-case with underscore)
- `viz{N}_{description}.png` — Generated visualization outputs
- `{topic}_доклад.docx` — Report documents in Russian

**Directories:**
- kebab-case: `volta-banking/`
- Lowercase for utility directories: `utils/`, `data/`, `doc/`

**Special Patterns:**
- `volta_*.py` — Volta Neobank analysis scripts
- `viz*.png` — Auto-generated matplotlib outputs

## Where to Add New Code

**New Analysis:**
- Primary code: Root directory (`volta_{topic}.py`)
- Data: `data/{dataset}.csv`
- Visualization outputs: Root directory (`viz{N}_{description}.png`)

**New Utility:**
- Implementation: `utils/{module_name}.py`
- Export: Add to `utils/__init__.py`

**New Report:**
- Primary code: `doc/` or root
- Data references: Use relative paths from repo root

## Special Directories

**.venv/**
- Purpose: Python virtual environment (managed by uv)
- Source: Created by `uv sync` or `uv venv`
- Committed: No (not in `.gitignore` explicitly, but should be ignored)

**presentations/**
- Purpose: Portfolio slide decks
- Source: Manually created/exported
- Committed: Yes

---

*Structure analysis: 2026-05-01*
*Update when directory structure changes*
