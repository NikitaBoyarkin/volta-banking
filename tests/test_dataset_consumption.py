"""REQ-003 AC3 — every generated dataset must have a reader.

The audit (PA-07) found three generated CSVs with zero readers while their
generators stayed in ``make data``. This test binds the requirement that no
CSV in ``data/`` is dead weight: each basename must be mentioned by at least
one analysis or test under ``scripts/`` or ``tests/``.

Two exclusions keep the check honest:

* **Generator scripts** (``scripts/generate_*.py``) are producing the file, not
  consuming it — a generator mentioning its own output proves nothing.
* **This test file itself** is excluded from the search. Otherwise a test that
  listed the expected basenames would satisfy its own condition vacuously.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
SCRIPTS_DIR = REPO_ROOT / "scripts"
TESTS_DIR = REPO_ROOT / "tests"
SELF = Path(__file__).resolve()

# The three PA-07 datasets the feature-adoption analysis was built to consume.
PA07_DATASETS = (
    "volta_feature_events.csv",
    "volta_referrals.csv",
    "volta_campaigns.csv",
)


def _reader_sources() -> dict[Path, str]:
    """Python sources that may consume a dataset, minus generators and this test."""
    sources: dict[Path, str] = {}
    for directory in (SCRIPTS_DIR, TESTS_DIR):
        for path in sorted(directory.rglob("*.py")):
            if path.resolve() == SELF:
                continue
            if path.parent == SCRIPTS_DIR and path.name.startswith("generate_"):
                continue
            sources[path] = path.read_text(encoding="utf-8", errors="ignore")
    return sources


def test_every_data_csv_has_a_non_generator_reader() -> None:
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    assert csv_files, "No CSV files found in data/ — the check has nothing to inspect"

    sources = _reader_sources()
    assert sources, "No reader sources found under scripts/ or tests/"

    unread = [
        csv.name for csv in csv_files if not any(csv.name in text for text in sources.values())
    ]

    assert not unread, (
        "Generated datasets with no analysis or test reader (REQ-003 AC3): "
        f"{unread}. Add an analysis that reads them or remove the generator."
    )


def test_pa07_datasets_are_loaded_by_the_feature_adoption_analysis() -> None:
    """The three PA-07 files must be *loaded* by the new module, not just named."""
    analysis = SCRIPTS_DIR / "volta_feature_adoption.py"
    assert analysis.exists(), "scripts/volta_feature_adoption.py is missing"

    source = analysis.read_text(encoding="utf-8")
    for name in PA07_DATASETS:
        assert f'data_path("{name}")' in source, (
            f"{name} is not loaded through data_path() in {analysis.name}"
        )
