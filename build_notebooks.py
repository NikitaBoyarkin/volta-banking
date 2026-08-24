"""Build + execute presentation notebooks for the four core Volta projects.

Creates `notebooks/01_funnel.ipynb` .. `04_segmentation.ipynb`, each with a
markdown intro and a single code cell that runs the module's `main()`. Uses
`nbconvert --execute` so outputs are embedded (an "executed notebook").

Run:  uv run python build_notebooks.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

PROJECTS = [
    ("01_funnel", "volta_funnel_analysis", "Funnel Analysis — where users drop off in onboarding"),
    ("02_ab_test", "volta_ab_testing", "A/B Test — KYC progress bar lift"),
    ("03_retention", "volta_retention_analysis", "Retention & Cohort — did the fix hold?"),
    ("04_segmentation", "volta_segmentation", "User Segmentation — who are the users?"),
]

NOTEBOOK_DIR = Path(__file__).resolve().parent / "notebooks"
TIMEOUT_SECONDS = 600


def build(name: str, module: str, title: str) -> nbformat.NotebookNode:
    cells = [
        new_markdown_cell(f"# {title}\n\nVolta Neobank portfolio — {module}."),
        new_code_cell(f"from {module} import main\n\nmain()"),
    ]
    return new_notebook(
        cells=cells,
        metadata={"kernelspec": {"name": "volta", "display_name": "volta", "language": "python"}},
    )


def execute(nb: nbformat.NotebookNode) -> nbformat.NotebookNode:
    ep = ExecutePreprocessor(timeout=TIMEOUT_SECONDS, kernel_name="volta")
    ep.preprocess(nb, {"metadata": {"path": str(NOTEBOOK_DIR.parent)}})
    return nb


def main() -> None:
    NOTEBOOK_DIR.mkdir(exist_ok=True)
    for name, module, title in PROJECTS:
        nb = build(name, module, title)
        nb = execute(nb)
        path = NOTEBOOK_DIR / f"{name}.ipynb"
        nbformat.write(nb, path)
        print(f"Wrote executed notebook: {path}")
    print("Done.")


if __name__ == "__main__":
    main()
