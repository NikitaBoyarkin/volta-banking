"""Visualization helpers for Volta portfolio charts.

Adds a consistent "description above, findings below" wrapper around
matplotlib figures so portfolio charts are self-contained.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt


def add_chart_context(
    fig: plt.Figure,
    title: str,
    description: str,
    findings: Sequence[str],
    title_size: int = 14,
    desc_size: int = 10,
    findings_size: int = 8,
    findings_color: str = "#E0E0E0",
    findings_box_color: str = "#2A2A2A",
    top_padding: float = 0.12,
    bottom_padding: float = 0.22,
) -> plt.Figure:
    """Add a description above the axes and a findings box below them.

    This makes charts self-contained for READMEs, decks, and recruiter review.

    Parameters
    ----------
    fig
        Matplotlib figure to annotate.
    title
        Short chart title placed at the very top.
    description
        One-sentence description of what the chart shows (subtitle).
    findings
        Bullet points rendered below the plot area.
    title_size, desc_size, findings_size
        Font sizes for the three text blocks.
    findings_color
        Text color for findings (default light gray for dark_background).
    findings_box_color
        Background color for the findings box.
    top_padding
        Fraction of figure height reserved above the subplots for title/description.
    bottom_padding
        Fraction of figure height reserved below the subplots for findings.

    Returns
    -------
    The same figure, for chaining.

    Notes
    -----
    Do NOT call ``fig.tight_layout()`` after this helper — it will overwrite the
    manual margins. Call ``fig.savefig(..., bbox_inches="tight")`` directly.
    """
    fig.subplots_adjust(top=1.0 - top_padding, bottom=bottom_padding)

    fig.suptitle(
        title,
        fontsize=title_size,
        fontweight="bold",
        y=0.98,
        va="top",
    )
    fig.text(
        0.5,
        0.94,
        description,
        ha="center",
        va="top",
        fontsize=desc_size,
        style="italic",
        color="#B0B0B0",
    )

    bullet_text = "\n".join(f"• {line}" for line in findings)
    fig.text(
        0.5,
        0.03,
        bullet_text,
        ha="center",
        va="bottom",
        fontsize=findings_size,
        color=findings_color,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": findings_box_color,
            "edgecolor": "#444444",
            "linewidth": 1,
        },
    )
    return fig


def save_chart(fig: plt.Figure, out: Path, dpi: int = 150) -> Path:
    """Save a chart and close the figure to avoid memory leaks."""
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out
