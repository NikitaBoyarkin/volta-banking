"""REQ-005 AC3 — the mypy gate must cover every analysis module.

The audit (PA-06) found 9 of the 23 ``scripts/volta_*.py`` analyses outside
``[tool.mypy] files``, including the flagship funnel / A/B / retention /
segmentation modules: adding a module to the repo did not add it to the gate,
and nothing noticed. These tests bind the claim "mypy covers all analyses" to
a mechanism:

* A new ``scripts/volta_*.py`` that is not listed in ``[tool.mypy] files``
  fails ``test_every_analysis_is_listed_in_mypy`` — the gate cannot drift.
* A module that gains ``# mypy: ignore-errors`` without being named in the
  pyproject comment fails ``test_ignore_marked_modules_are_documented`` — the
  "listed in one place" half of AC2 stays true.

The config is read with ``tomllib`` and the filesystem with ``pathlib``; no
shell globs, so the test cannot be satisfied by an expansion quirk. ``tomllib``
is stdlib from 3.11 on; the repo pins 3.14 in ``.python-version`` (CI reads the
same file), so the nominal ``requires-python >=3.10`` floor is not exercised.
"""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
PYPROJECT = REPO_ROOT / "pyproject.toml"

MYPY_SECTION = "[tool.mypy]"
IGNORE_MARKER = "mypy: ignore-errors"
# Names the pyproject comment lists when documenting the ignore-errors markers.
# Only analysis modules are matched, so unrelated paths in the same comment
# block (e.g. the test file that enforces this) are ignored.
COMMENT_MODULE_RE = re.compile(r"\b(volta_[a-z0-9_]+\.py)\b")


def _mypy_config() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["mypy"]


def _analysis_modules() -> set[str]:
    """Every on-disk analysis module, as a repo-relative posix path."""
    return {path.relative_to(REPO_ROOT).as_posix() for path in SCRIPTS_DIR.glob("volta_*.py")}


def _mypy_files() -> set[str]:
    return {Path(entry.replace("\\", "/")).as_posix() for entry in _mypy_config()["files"]}


def _commented_modules() -> set[str]:
    """Module names named in comments at the top of the ``[tool.mypy]`` block."""
    section = PYPROJECT.read_text(encoding="utf-8").split(MYPY_SECTION, 1)[1]
    comment_lines = [line for line in section.splitlines() if line.lstrip().startswith("#")]
    names: set[str] = set()
    for line in comment_lines:
        names.update(COMMENT_MODULE_RE.findall(line))
    return names


def _ignore_marked_modules() -> set[str]:
    """Modules whose first lines carry ``# mypy: ignore-errors``."""
    marked = set()
    for path in sorted(SCRIPTS_DIR.glob("*.py")):
        head = path.read_text(encoding="utf-8").splitlines()[:5]
        if any(IGNORE_MARKER in line for line in head):
            marked.add(path.name)
    return marked


def test_every_analysis_is_listed_in_mypy() -> None:
    on_disk = _analysis_modules()
    # Guard against a vacuous pass: the repo ships 20+ analyses.
    assert len(on_disk) >= 20, f"only found {len(on_disk)} analyses under {SCRIPTS_DIR}"

    missing = sorted(on_disk - _mypy_files())
    assert not missing, (
        "these analysis modules are not covered by [tool.mypy] files in pyproject.toml: "
        + ", ".join(missing)
    )


def test_ignore_marked_modules_are_documented() -> None:
    marked = _ignore_marked_modules()
    documented = _commented_modules()
    assert marked, "expected the legacy pandas analyses to carry '# mypy: ignore-errors'"

    undocumented = sorted(marked - documented)
    assert not undocumented, (
        "modules silenced with '# mypy: ignore-errors' must be named in the "
        "[tool.mypy] comment in pyproject.toml: " + ", ".join(undocumented)
    )

    stale = sorted(documented - marked)
    assert not stale, (
        "pyproject.toml's [tool.mypy] comment names modules that no longer carry "
        "'# mypy: ignore-errors': " + ", ".join(stale)
    )
