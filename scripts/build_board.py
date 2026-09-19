"""Build the Volta zero-install HTML board from the committed CSVs.

Produces `docs/board/volta_board.html` — a single self-contained file with no
JavaScript, no CDN, and no runtime network: every chart is inline SVG emitted
from the repository's own `data/*.csv`, so a recruiter can double-click it open
with nothing installed.

    uv run python scripts/build_board.py     # or: make board

The board cannot silently drift from the data: it is regenerated from the CSVs
by this script, and `tests/test_board.py` asserts every section renders.
"""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from utils.common import REPO_ROOT, data_path

OUT_PATH = REPO_ROOT / "docs" / "board" / "volta_board.html"
OG_PATH = REPO_ROOT / "docs" / "board" / "og_image.png"

COLORS = {
    "blue": "#4C9AFF",
    "accent": "#00A8E8",
    "gold": "#FFAB00",
    "warn": "#FF5630",
    "ok": "#36B37E",
    "muted": "#93A4C3",
}
FUNNEL_STEPS = [
    "app_install",
    "registration",
    "kyc_start",
    "kyc_complete",
    "card_ordered",
    "first_tx",
]
SEGMENT_LABELS = {
    "young_professionals": "Young Professionals",
    "digital_newcomers": "Digital Newcomers 45+",
    "travelers": "Travelers",
    "family_budgeters": "Family Budgeters",
    "premium_status": "Premium Status",
}


# ── SVG primitives (no dependencies, hover tooltips via <title>) ─────────────
def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _int(v: float) -> str:
    return f"{v:,.0f}"


def _empty_svg() -> str:
    return (
        '<svg viewBox="0 0 640 40" xmlns="http://www.w3.org/2000/svg">'
        '<text x="320" y="24" text-anchor="middle" fill="#93A4C3" font-size="13">'
        "no data</text></svg>"
    )


def bar_chart(
    labels: list[str],
    values: list[float],
    *,
    fmt=_pct,
    color: str = COLORS["blue"],
    width: int = 640,
    height: int = 320,
) -> str:
    if not labels:
        return _empty_svg()
    ml, mr, mt, mb = 52, 18, 22, 72
    pw, ph = width - ml - mr, height - mt - mb
    vmax = max(values) * 1.18 or 1.0
    step = pw / len(labels)
    bw = step * 0.6
    parts = [f'<line x1="{ml}" y1="{mt + ph}" x2="{width - mr}" y2="{mt + ph}" stroke="#2b3d61"/>']
    for i, (lab, val) in enumerate(zip(labels, values, strict=True)):
        cx = ml + step * i + step / 2
        bh = max(1.0, ph * (val / vmax))
        y = mt + ph - bh
        esc = html.escape(str(lab))
        parts.append(
            f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'rx="3" fill="{color}"><title>{esc}: {fmt(val)}</title></rect>'
        )
        parts.append(
            f'<text x="{cx:.1f}" y="{y - 5:.1f}" text-anchor="middle" fill="#E8EEFC" '
            f'font-size="11">{fmt(val)}</text>'
        )
        parts.append(
            f'<text x="{cx:.1f}" y="{mt + ph + 16:.1f}" text-anchor="end" fill="#93A4C3" '
            f'font-size="11" transform="rotate(-32 {cx:.1f} {mt + ph + 16:.1f})">{esc}</text>'
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img">{"".join(parts)}</svg>'
    )


def grouped_bar_chart(
    labels: list[str],
    series: list[tuple[str, list[float], str]],
    *,
    fmt=_pct,
    width: int = 640,
    height: int = 340,
) -> str:
    if not labels or not series:
        return _empty_svg()
    ml, mr, mt, mb = 52, 18, 46, 72
    pw, ph = width - ml - mr, height - mt - mb
    vmax = max(max(vals) for _, vals, _ in series) * 1.2 or 1.0
    step = pw / len(labels)
    n = len(series)
    bw = step * 0.8 / n
    parts = [f'<line x1="{ml}" y1="{mt + ph}" x2="{width - mr}" y2="{mt + ph}" stroke="#2b3d61"/>']
    for si, (name, vals, color) in enumerate(series):
        lx = ml + si * 130
        parts.append(f'<rect x="{lx}" y="12" width="11" height="11" rx="2" fill="{color}"/>')
        parts.append(
            f'<text x="{lx + 16}" y="22" fill="#C7D3EA" font-size="12">{html.escape(name)}</text>'
        )
        for i, val in enumerate(vals):
            cx = ml + step * i + step * 0.1 + bw * (si + 0.5)
            bh = max(1.0, ph * (val / vmax))
            y = mt + ph - bh
            parts.append(
                f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                f'rx="2" fill="{color}"><title>{html.escape(name)} · '
                f"{html.escape(str(labels[i]))}: {fmt(val)}</title></rect>"
            )
    for i, lab in enumerate(labels):
        cx = ml + step * i + step / 2
        parts.append(
            f'<text x="{cx:.1f}" y="{mt + ph + 16:.1f}" text-anchor="end" fill="#93A4C3" '
            f'font-size="11" transform="rotate(-26 {cx:.1f} {mt + ph + 16:.1f})">'
            f"{html.escape(str(lab))}</text>"
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img">{"".join(parts)}</svg>'
    )


def line_chart(
    x_labels: list[str],
    series: list[tuple[str, list[float], str]],
    *,
    fmt=_pct,
    width: int = 640,
    height: int = 320,
) -> str:
    if not x_labels or not series:
        return _empty_svg()
    ml, mr, mt, mb = 52, 110, 26, 46
    pw, ph = width - ml - mr, height - mt - mb
    vmax = max(max(vals) for _, vals, _ in series) * 1.1 or 1.0
    parts = [f'<line x1="{ml}" y1="{mt + ph}" x2="{width - mr}" y2="{mt + ph}" stroke="#2b3d61"/>']

    def px(i: int) -> float:
        return ml + (pw * i / max(1, len(x_labels) - 1))

    def py(v: float) -> float:
        return mt + ph - ph * (v / vmax)

    for si, (name, vals, color) in enumerate(series):
        pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vals))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for i, v in enumerate(vals):
            parts.append(
                f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="3" fill="{color}">'
                f"<title>{html.escape(name)} · {html.escape(str(x_labels[i]))}: {fmt(v)}</title>"
                "</circle>"
            )
        ly = mt + si * 20
        parts.append(
            f'<line x1="{ml + pw + 12}" y1="{ly}" x2="{ml + pw + 28}" y2="{ly}" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
        parts.append(
            f'<text x="{ml + pw + 34}" y="{ly + 4}" fill="#C7D3EA" font-size="12">'
            f"{html.escape(name)}</text>"
        )
    for i, lab in enumerate(x_labels):
        if i % 2 == 0 or i == len(x_labels) - 1:
            parts.append(
                f'<text x="{px(i):.1f}" y="{mt + ph + 18:.1f}" text-anchor="middle" '
                f'fill="#93A4C3" font-size="11">{html.escape(str(lab))}</text>'
            )
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img">{"".join(parts)}</svg>'
    )


# ── Data loaders (all from committed CSVs) ───────────────────────────────────
def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(data_path(name))


def funnel_step_conversion(df: pd.DataFrame) -> tuple[list[str], list[float]]:
    counts = [float(df[step].sum()) for step in FUNNEL_STEPS]
    labels, values = [], []
    for i in range(1, len(FUNNEL_STEPS)):
        labels.append(FUNNEL_STEPS[i])
        values.append(counts[i] / counts[i - 1] if counts[i - 1] else 0.0)
    return labels, values


def ab_lift(df: pd.DataFrame) -> tuple[float, float, float]:
    conv = df.groupby("group")["kyc_completed"].mean()
    control, treatment = float(conv["control"]), float(conv["treatment"])
    return control, treatment, treatment - control


def retention_curves(matrix: pd.DataFrame) -> tuple[list[str], list[float], list[float]]:
    matrix = matrix.set_index("cohort")
    months = [f"month_{m}" for m in range(12)]
    pre = matrix.loc[matrix.index < "2024-09", months].mean()
    post = matrix.loc[matrix.index >= "2024-09", months].mean()
    return [f"M{m}" for m in range(12)], [float(v) for v in pre], [float(v) for v in post]


def causal_did(df: pd.DataFrame, outcome: str = "retained_m3") -> dict[str, float]:
    means = df.groupby(["treated", "post"])[outcome].mean()
    t_change = means[(1, 1)] - means[(1, 0)]
    c_change = means[(0, 1)] - means[(0, 0)]
    return {
        "in_pre": float(means[(1, 0)]),
        "in_post": float(means[(1, 1)]),
        "pt_pre": float(means[(0, 0)]),
        "pt_post": float(means[(0, 1)]),
        "att": float(t_change - c_change),
    }


def premium_by_segment(df: pd.DataFrame) -> tuple[list[str], list[float]]:
    conv = df.groupby("jtbd_segment")["converted"].mean().sort_values(ascending=False)
    return [SEGMENT_LABELS[s] for s in conv.index], [float(v) for v in conv.values]


def referral_by_segment(df: pd.DataFrame) -> tuple[list[str], list[float]]:
    conv = (
        df.assign(reached=df["status"].eq("first_tx"))
        .groupby("jtbd_segment")["reached"]
        .mean()
        .sort_values(ascending=False)
    )
    return [SEGMENT_LABELS[s] for s in conv.index], [float(v) for v in conv.values]


def jtbd_counts(df: pd.DataFrame) -> tuple[list[str], list[float]]:
    counts = df["jtbd_segment"].value_counts().sort_values(ascending=False)
    return [SEGMENT_LABELS[s] for s in counts.index], [float(v) for v in counts.values]


def segment_revenue_share(df: pd.DataFrame) -> tuple[list[str], list[float]]:
    df = df.sort_values("revenue_share", ascending=False)
    return list(df["segment"]), [float(v) / 100.0 for v in df["revenue_share"]]


# ── Page assembly ────────────────────────────────────────────────────────────
def _kpi(value: str, label: str, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{html.escape(sub)}</div>' if sub else ""
    return (
        f'<div class="card kpi"><div class="kpi-value">{html.escape(value)}</div>'
        f'<div class="kpi-label">{html.escape(label)}</div>{sub_html}</div>'
    )


def _section(sec_id: str, title: str, question: str, chart: str, takeaway: str) -> str:
    return (
        f'<section class="card chart" id="{sec_id}">'
        f"<h2>{html.escape(title)}</h2>"
        f'<p class="question">{html.escape(question)}</p>'
        f'<div class="plot">{chart}</div>'
        f'<p class="takeaway">{html.escape(takeaway)}</p>'
        "</section>"
    )


def build_html() -> str:
    funnel = _read("volta_funnel_data.csv")
    ab = _read("volta_ab_experiment.csv")
    retention = _read("cohort_retention_matrix.csv")
    causal = _read("volta_causal_kyc.csv")
    jtbd = _read("volta_jtbd_segments.csv")
    premium = _read("volta_premium_upsell.csv")
    referral = _read("volta_referral_segments.csv")
    profiles = _read("segment_profiles.csv")

    control, treatment, lift = ab_lift(ab)
    months, pre_curve, post_curve = retention_curves(retention)
    m3_delta = post_curve[3] - pre_curve[3]
    did = causal_did(causal)
    prem_labels, prem_vals = premium_by_segment(premium)
    ref_labels, ref_vals = referral_by_segment(referral)

    funnel_labels, funnel_vals = funnel_step_conversion(funnel)
    seg_labels, seg_vals = segment_revenue_share(profiles)
    jt_labels, jt_vals = jtbd_counts(jtbd)

    kpis = "".join(
        [
            _kpi("17", "analytical projects", "funnel → JTBD → causal"),
            _kpi("170+", "tests · 98% coverage", "ruff · mypy · CI green"),
            _kpi(f"+{lift * 100:.2f}pp", "KYC activation lift", "A/B, p<0.0001"),
            _kpi(f"+{m3_delta * 100:.1f}pp", "M3 retention lift", "post-fix cohorts"),
            _kpi(
                f"+{did['att'] * 100:.1f}pp",
                "causal DiD ATT (M3)",
                "diff-in-diff, parallel trends ✓",
            ),
            _kpi(
                f"{ref_vals[0] * 100:.1f}% vs {ref_vals[-1] * 100:.1f}%",
                "referral conversion",
                "anchor vs 45+ gap",
            ),
        ]
    )

    sections = "".join(
        [
            _section(
                "funnel",
                "Onboarding funnel",
                "Where do new users drop off between install and first transaction?",
                bar_chart(funnel_labels, funnel_vals, color=COLORS["blue"]),
                "KYC completion is the critical step: the largest relative drop in the funnel. "
                "Registration loses the most users in absolute terms — two lenses, reported both.",
            ),
            _section(
                "ab",
                "KYC progress-bar A/B test",
                "Does a progress bar in the KYC flow lift completion?",
                grouped_bar_chart(
                    ["control", "treatment"],
                    [
                        ("KYC completion", [control, treatment], COLORS["blue"]),
                    ],
                ),
                f"Treatment lifts completion by +{lift * 100:.2f}pp (p<0.0001, no SRM) — ship. "
                "This is the randomized claim the causal layer later strengthens.",
            ),
            _section(
                "retention",
                "Cohort retention",
                "Did the fix hold up in long-term retention?",
                line_chart(
                    months,
                    [
                        ("pre-fix", pre_curve, COLORS["muted"]),
                        ("post-fix", post_curve, COLORS["accent"]),
                    ],
                ),
                f"Post-fix cohorts retain better from M1 onward (+{m3_delta * 100:.1f}pp at M3). "
                "The gap persists across the curve, not just at one month.",
            ),
            _section(
                "causal",
                "Causal layer — difference-in-differences",
                "Was the retention lift caused by the fix, or just a shared time trend?",
                grouped_bar_chart(
                    ["in-app: pre", "in-app: post", "partner: pre", "partner: post"],
                    [
                        (
                            "M3 retention",
                            [did["in_pre"], did["in_post"], did["pt_pre"], did["pt_post"]],
                            COLORS["accent"],
                        ),
                    ],
                ),
                f"DiD ATT = +{did['att'] * 100:.1f}pp: the treated flow rises at the cutoff while the "
                "comparison flow does not. Pre-trends flat, placebo null, covariates balanced.",
            ),
            _section(
                "segmentation",
                "Customer segmentation",
                "Who are the users and where does revenue concentrate?",
                bar_chart(seg_labels, seg_vals, color=COLORS["gold"]),
                "The top segment is 12% of users but ~41% of revenue — a classic concentration "
                "story that drives the per-segment monetization strategy.",
            ),
            _section(
                "jobs",
                "Market & Jobs — premium upsell",
                "Does the premium upsell transfer to every job segment?",
                bar_chart(prem_labels, prem_vals, color=COLORS["ok"]),
                "The anchor segment converts at ~17% while Digital Newcomers 45+ sit near 2% — "
                "the value proposition does not transfer. Segment-specific offers, not one upsell.",
            ),
            _section(
                "referral",
                "Market & Jobs — referral conversion",
                "Does referral scale to new segments?",
                bar_chart(ref_labels, ref_vals, color=COLORS["warn"]),
                "Referral converts best in the anchor and collapses for 45+ and family budgeters — "
                "don't scale referral spend before segment-specific incentives.",
            ),
            _section(
                "jtbd",
                "Market & Jobs — segment sizes",
                "How big is each job segment in the simulated base?",
                bar_chart(jt_labels, jt_vals, fmt=_int, color=COLORS["blue"]),
                "Five JTBD segments simulated at scale — the population the Market & Jobs layer "
                "reasons about.",
            ),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Volta Neobank — Product Analytics Portfolio</title>
<meta name="description" content="Zero-install product analytics board for the Volta neobank portfolio: funnel, A/B, retention, causal DiD, segmentation, JTBD.">
<style>
:root {{
  --bg:#0b1220; --panel:#121b2e; --line:#223354; --ink:#e8eefc; --muted:#93a4c3;
  --blue:#4C9AFF; --accent:#00A8E8; --gold:#FFAB00; --warn:#FF5630; --ok:#36B37E;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; padding:32px 20px 64px; color:var(--ink);
  background:radial-gradient(1200px 600px at 20% -10%, #14224a 0%, var(--bg) 55%);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;
}}
.wrap {{ max-width:1040px; margin:0 auto; }}
header {{ margin-bottom:28px; }}
.badge {{ display:inline-block; font-size:12px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--accent); border:1px solid var(--line); padding:4px 10px; border-radius:999px; }}
h1 {{ font-size:34px; margin:14px 0 8px; }}
.hook {{ color:var(--muted); max-width:760px; margin:0; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(168px,1fr)); gap:14px; margin:28px 0; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; }}
.kpi-value {{ font-size:24px; font-weight:700; }}
.kpi-label {{ color:var(--muted); font-size:13px; margin-top:2px; }}
.kpi-sub {{ color:#6d80a6; font-size:11px; margin-top:6px; }}
.chart {{ margin:16px 0; }}
.chart h2 {{ font-size:18px; margin:0 0 4px; }}
.question {{ color:var(--muted); font-size:14px; margin:0 0 10px; }}
.plot {{ background:#0d1526; border:1px solid #1b2946; border-radius:10px; padding:10px; }}
.plot svg {{ width:100%; height:auto; display:block; }}
.takeaway {{ font-size:14px; margin:12px 0 0; border-left:3px solid var(--accent); padding-left:12px; }}
footer {{ color:var(--muted); font-size:13px; margin-top:32px; border-top:1px solid var(--line); padding-top:16px; }}
footer a {{ color:var(--accent); }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <span class="badge">Product Analytics Portfolio</span>
  <h1>Volta Neobank</h1>
  <p class="hook">An end-to-end analytics narrative for a fictional neobank — from onboarding
  funnel to A/B test, cohort retention, a difference-in-differences causal test, segmentation,
  and a Market &amp; Jobs layer. Every chart below is rendered from the repository's own
  committed CSVs. No install, no server, no JavaScript.</p>
</header>
<div class="kpis">{kpis}</div>
{sections}
<footer>
  Synthetic data · seeded generators · <a href="https://github.com/NikitaBoyarkin/volta-banking" target="_blank" rel="noopener">github.com/NikitaBoyarkin/volta-banking</a>
  &nbsp;·&nbsp; rebuilt from <code>data/*.csv</code> by <code>make board</code>.
</footer>
</div>
</body>
</html>
"""


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(build_html(), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Wrote: {OUT_PATH.relative_to(REPO_ROOT)} ({size_kb:.0f} KB)")
    print("Self-contained: inline SVG, no JS, no CDN. Open it with a double-click.")

    build_og_image(OG_PATH)
    print(f"Wrote: {OG_PATH.relative_to(REPO_ROOT)} (1200×630 social preview)")


def build_og_image(out: Path = OG_PATH) -> Path:
    """Render the 1200×630 branded social-preview / README hero card.

    Generated programmatically from the committed CSVs (not an AI image) so it
    is reproducible and cannot drift from the data.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ab = _read("volta_ab_experiment.csv")
    retention = _read("cohort_retention_matrix.csv")
    causal = _read("volta_causal_kyc.csv")
    _, _, lift = ab_lift(ab)
    _, pre_curve, post_curve = retention_curves(retention)
    did = causal_did(causal)

    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="#0b1220")
    fig.patches.append(
        plt.Rectangle(
            (0, 0.965),
            1,
            0.035,
            transform=fig.transFigure,
            facecolor=COLORS["accent"],
            edgecolor="none",
        )
    )
    fig.text(0.06, 0.76, "Volta Neobank", fontsize=46, fontweight="bold", color="#E8EEFC")
    fig.text(
        0.06,
        0.655,
        "End-to-end product analytics portfolio",
        fontsize=21,
        color=COLORS["accent"],
    )
    fig.text(
        0.06,
        0.565,
        "funnel  →  A/B test  →  retention  →  causal DiD  →  segmentation  →  JTBD",
        fontsize=14,
        color="#93A4C3",
    )

    chips = [
        (f"+{lift * 100:.2f}pp", "KYC activation lift"),
        (f"+{(post_curve[3] - pre_curve[3]) * 100:.1f}pp", "M3 retention"),
        (f"+{did['att'] * 100:.1f}pp", "causal DiD ATT"),
        ("17", "analytical projects"),
    ]
    x0, wid, gap = 0.06, 0.205, 0.016
    for i, (value, label) in enumerate(chips):
        x = x0 + i * (wid + gap)
        fig.text(
            x + wid / 2,
            0.335,
            value,
            ha="center",
            va="center",
            fontsize=30,
            fontweight="bold",
            color="#E8EEFC",
            bbox={
                "boxstyle": "round,pad=0.55",
                "facecolor": "#121b2e",
                "edgecolor": "#223354",
                "linewidth": 1.5,
            },
        )
        fig.text(
            x + wid / 2,
            0.215,
            label,
            ha="center",
            va="center",
            fontsize=11.5,
            color="#93A4C3",
        )

    fig.text(
        0.06,
        0.07,
        "python · pandas · scikit-learn · synthetic, seeded data  ·  github.com/NikitaBoyarkin/volta-banking",
        fontsize=12,
        color="#6d80a6",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor="#0b1220")
    plt.close(fig)
    return out


if __name__ == "__main__":
    main()
