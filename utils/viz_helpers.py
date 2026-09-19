"""Visualization helpers for Volta portfolio charts.

Two jobs:

* ``apply_style`` — one light, README-friendly theme shared by every chart.
* ``save_chart_report`` — persist a clean PNG (title + axes, no conclusions
  baked into the image) plus a companion Markdown sidecar that carries the
  conclusions as prose below the chart.

The old behaviour — drawing a findings box *inside* the figure — overlapped
axis labels and duplicated the Markdown narrative, so it was removed.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt

# ── Theme ────────────────────────────────────────────────────────────────────
# Brand palette readable on a white background. Blue is the primary series
# colour; orange/green/red are accents, slate is for muted/reference marks.
PALETTE: list[str] = [
    "#2563EB",  # blue   — primary
    "#F59E0B",  # orange — secondary
    "#10B981",  # green  — positive
    "#EF4444",  # red    — negative / alert
    "#8B5CF6",  # violet
    "#14B8A6",  # teal
    "#94A3B8",  # slate  — muted
]

TITLE_COLOR = "#111827"
DESC_COLOR = "#6B7280"
AXIS_COLOR = "#1F2937"
TICK_COLOR = "#475569"
GRID_COLOR = "#E2E8F0"
EDGE_COLOR = "#CBD5E1"


def ru_num(value: float, digits: int = 0) -> str:
    """Format a number the Russian way: space thousands, comma decimals.

    ``ru_num(2682) -> "2 682"`` and ``ru_num(56.6, 1) -> "56,6"``. Use a
    narrow no-break space so numbers never wrap across lines.
    """
    return f"{value:,.{digits}f}".replace(",", "\u202f").replace(".", ",")


def apply_style() -> None:
    """Apply the shared light theme (idempotent).

    Uses seaborn's ``whitegrid`` as the base and pins the palette/text colours
    so charts are legible on the white README and portfolio site.
    """
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.facecolor": "#FFFFFF",
            "axes.facecolor": "#FFFFFF",
            "savefig.facecolor": "#FFFFFF",
            "axes.edgecolor": EDGE_COLOR,
            "axes.labelcolor": AXIS_COLOR,
            "text.color": AXIS_COLOR,
            "xtick.color": TICK_COLOR,
            "ytick.color": TICK_COLOR,
            "grid.color": GRID_COLOR,
            "axes.prop_cycle": plt.cycler(color=PALETTE),
            "font.size": 10,
        }
    )


def add_chart_context(
    fig: plt.Figure,
    title: str,
    description: str = "",
    *,
    title_size: int = 14,
    desc_size: int = 10,
    top_padding: float = 0.12,
) -> plt.Figure:
    """Draw a figure title and optional one-line description above the axes.

    Findings are intentionally *not* drawn here — they belong in the Markdown
    sidecar produced by :func:`save_chart_report`.

    Parameters
    ----------
    fig
        Matplotlib figure to annotate.
    title
        Short chart title placed at the very top.
    description
        One-sentence subtitle (English, matches the chart's own labels).
    title_size, desc_size
        Font sizes for the two text blocks.
    top_padding
        Fraction of figure height reserved above the subplots.

    Returns
    -------
    The same figure, for chaining.

    Notes
    -----
    Do NOT call ``fig.tight_layout()`` after this helper — it will overwrite the
    manual margins. Call ``fig.savefig(..., bbox_inches="tight")`` directly.
    """
    fig.subplots_adjust(top=1.0 - top_padding)

    fig.suptitle(
        title,
        fontsize=title_size,
        fontweight="bold",
        y=0.98,
        va="top",
        color=TITLE_COLOR,
    )
    if description:
        fig.text(
            0.5,
            0.94,
            description,
            ha="center",
            va="top",
            fontsize=desc_size,
            style="italic",
            color=DESC_COLOR,
        )
    return fig


def save_chart(fig: plt.Figure, out: Path, dpi: int = 150) -> Path:
    """Save a chart and close the figure to avoid memory leaks."""
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out


def render_report(
    *,
    title: str,
    png_name: str,
    findings: Sequence[str],
    description_ru: str = "",
    script: str | None = None,
    source: str | None = None,
) -> str:
    """Render the Markdown sidecar: chart on top, conclusions below."""
    parts: list[str] = [f"# {title}", "", f"![{title}]({png_name})", ""]
    if description_ru:
        parts += [f"*{description_ru}*", ""]
    parts += ["## Выводы", ""]
    parts += [f"- {line}" for line in findings]
    parts += [""]

    footer_bits: list[str] = []
    if script:
        footer_bits.append(f"`{script}`")
    if source:
        footer_bits.append(f"данные: `{source}`")
    if footer_bits:
        parts += ["---", f"<sub>Источник: {' · '.join(footer_bits)}</sub>", ""]

    return "\n".join(parts)


def save_chart_report(
    fig: plt.Figure,
    out: Path,
    *,
    title: str,
    findings: Sequence[str],
    description_ru: str = "",
    script: str | None = None,
    source: str | None = None,
    dpi: int = 150,
) -> Path:
    """Save a clean PNG plus its ``.md`` sidecar (chart, then ``## Выводы``).

    The figure must already carry its own title (via :func:`add_chart_context`
    or ``ax.set_title``); this helper does not add one. The PNG is written
    next to the Markdown file, which references it by relative name.
    """
    out = Path(out)
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    out.with_suffix(".md").write_text(
        render_report(
            title=title,
            png_name=out.name,
            findings=findings,
            description_ru=description_ru,
            script=script,
            source=source,
        ),
        encoding="utf-8",
    )
    return out
