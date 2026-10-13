"""Volta EDA — figures (wave 2, flagship). 6 PNGs, light theme, dpi=300.

    /Users/nikitaboarkin/Desktop/00 ide/00 portfolio/.eda-tools/.venv/bin/python \
        reports/eda/scripts/plot_volta.py

Writes to reports/eda/figures/. Reads data/ only; never writes outside reports/eda/.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "font.family": ["DejaVu Sans", "sans-serif"],
        "axes.unicode_minus": False,
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
    }
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
OUT = ROOT / "reports" / "eda" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

ACCENT = "#2F6FED"
MUTED = "#9AA7BD"
BAD = "#E4572E"
GOOD = "#2E9E5B"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def save(fig, name: str) -> None:
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", OUT / name)


# ── load ─────────────────────────────────────────────────────────────────────
fun = pd.read_csv(DATA / "charts" / "funnel.csv")
ab = pd.read_csv(DATA / "volta_ab_experiment.csv")
coh = pd.read_csv(DATA / "cohort_retention_matrix.csv")

STEPS = ["app_install", "registration", "kyc_start", "kyc_complete", "card_ordered", "first_tx"]
counts = {s: int(fun[s].sum()) for s in STEPS}

# ── Fig 1: funnel counts + step conversion ───────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")

labels = [s.replace("_", " ") for s in STEPS]
vals = [counts[s] for s in STEPS]
bars = ax1.barh(range(len(STEPS))[::-1], vals, color=ACCENT, alpha=0.85, edgecolor="white")
ax1.set_yticks(range(len(STEPS))[::-1])
ax1.set_yticklabels(labels)
for i, v in zip(range(len(STEPS))[::-1], vals, strict=True):
    ax1.text(v + 120, i, f"{v:,}", va="center", fontsize=10)
ax1.set(xlabel="Users reaching step", ylabel="", title="Onboarding funnel — absolute reach")
ax1.set_xlim(0, 11200)

step_conv, lo_list, hi_list = [], [], []
for a, b in zip(STEPS[:-1], STEPS[1:], strict=True):
    k, n = counts[b], counts[a]
    step_conv.append(k / n)
    lo, hi = wilson(k, n)
    lo_list.append(lo)
    hi_list.append(hi)
x = np.arange(len(step_conv))
step_conv = np.array(step_conv)
err = np.array([step_conv - lo_list, hi_list - step_conv])
colors = [BAD if s < 0.6 else ACCENT for s in step_conv]
ax2.bar(x, step_conv, color=colors, alpha=0.88, edgecolor="white")
ax2.errorbar(x, step_conv, yerr=err, fmt="none", ecolor="#333", capsize=3, lw=1)
ax2.set_xticks(x)
ax2.set_xticklabels(
    [f"{a}\u2192{b}" for a, b in zip(STEPS[:-1], STEPS[1:], strict=True)],
    rotation=25,
    ha="right",
    fontsize=9,
)
for i, s in enumerate(step_conv):
    ax2.text(i, s + 0.015, f"{s:.1%}", ha="center", fontsize=9)
ax2.axhline(0.6, color=MUTED, ls="--", lw=1)
ax2.set(
    xlabel="Step transition",
    ylabel="Conversion rate",
    title="Step-over-step conversion (95% Wilson CI)\nKYC complete is the narrowest step",
)
ax2.set_ylim(0, 0.85)
save(fig, "fig1_funnel_conversion.png")

# ── Fig 2: first_tx by channel (lead segment gap) ────────────────────────────
g = fun.groupby("channel")["first_tx"].agg(["count", "sum", "mean"]).sort_values("mean")
ci = [wilson(int(r["sum"]), int(r["count"])) for _, r in g.iterrows()]
means = g["mean"].values
err = np.array(
    [
        [m - c[0] for m, c in zip(means, ci, strict=True)],
        [c[1] - m for m, c in zip(means, ci, strict=True)],
    ]
)
fig, ax = plt.subplots(figsize=(9, 5.5), layout="constrained")
cols = [BAD if m == means.min() else (GOOD if m == means.max() else ACCENT) for m in means]
ax.bar(
    range(len(g)),
    means,
    yerr=err,
    color=cols,
    alpha=0.88,
    edgecolor="white",
    capsize=4,
    error_kw={"ecolor": "#333", "lw": 1},
)
ax.set_xticks(range(len(g)))
ax.set_xticklabels(
    [f"{c}\n(n={int(n):,})" for c, n in zip(g.index, g["count"], strict=True)], fontsize=9
)
for i, m in enumerate(means):
    ax.text(i, m + 0.008, f"{m:.1%}", ha="center", fontsize=10)
ax.axhline(
    fun["first_tx"].mean(),
    color=MUTED,
    ls="--",
    lw=1.2,
    label=f"overall {fun['first_tx'].mean():.1%}",
)
ax.set(
    xlabel="Acquisition channel",
    ylabel="Install \u2192 first transaction rate",
    title="First-transaction conversion by channel\npaid_social 6.1% vs referral 17.8% (2.9\u00d7 gap)",
)
ax.legend(frameon=False)
save(fig, "fig2_first_tx_by_channel.png")

# ── Fig 3: A/B conversion control vs treatment ───────────────────────────────
c = ab[ab["group"] == "control"]["kyc_completed"].values
t = ab[ab["group"] == "treatment"]["kyc_completed"].values
cr, tr = c.mean(), t.mean()
ci_c = wilson(int(c.sum()), len(c))
ci_t = wilson(int(t.sum()), len(t))
fig, ax = plt.subplots(figsize=(7, 5.5), layout="constrained")
bars = ax.bar(
    ["Control", "Treatment\n(progress bar)"],
    [cr, tr],
    yerr=[[cr - ci_c[0], tr - ci_t[0]], [ci_c[1] - cr, ci_t[1] - tr]],
    color=[MUTED, ACCENT],
    alpha=0.9,
    edgecolor="white",
    capsize=6,
    error_kw={"ecolor": "#333", "lw": 1.2},
    width=0.55,
)
for i, v in enumerate([cr, tr]):
    ax.text(i, v + 0.02, f"{v:.2%}", ha="center", fontsize=12, fontweight="bold")
ax.annotate(
    "", xy=(1, tr), xytext=(0, cr), arrowprops={"arrowstyle": "<->", "color": BAD, "lw": 1.6}
)
ax.text(
    0.5,
    (cr + tr) / 2 + 0.01,
    "+5.72 pp\n(p < 0.0001)",
    ha="center",
    color=BAD,
    fontsize=11,
    fontweight="bold",
)
ax.set(
    ylabel="KYC completion rate",
    title="A/B test — KYC progress bar\nlift exceeds +5pp MDE, no SRM",
    ylim=(0, 0.72),
)
save(fig, "fig3_ab_conversion.png")

# ── Fig 4: HTE lift by segment (lead finding) ────────────────────────────────
rows = []
for col in ("age_group", "device", "channel"):
    for val in sorted(ab[col].unique()):
        sub = ab[ab[col] == val]
        cc = sub[sub["group"] == "control"]["kyc_completed"].values
        tt = sub[sub["group"] == "treatment"]["kyc_completed"].values
        tbl = np.array([[tt.sum(), len(tt) - tt.sum()], [cc.sum(), len(cc) - cc.sum()]])
        _, p, _, _ = stats.chi2_contingency(tbl)
        rows.append({"seg": f"{col}={val}", "lift": (tt.mean() - cc.mean()) * 100, "p": p})
hte = pd.DataFrame(rows).sort_values("lift")
fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
cols = [GOOD if p < 0.05 else MUTED for p in hte["p"]]
ax.barh(range(len(hte)), hte["lift"], color=cols, alpha=0.9, edgecolor="white")
ax.set_yticks(range(len(hte)))
ax.set_yticklabels(hte["seg"], fontsize=9)
ax.axvline(5.72, color=BAD, ls="--", lw=1.4, label="overall lift +5.72 pp")
for i, (lift, p) in enumerate(zip(hte["lift"], hte["p"], strict=True)):
    tag = f"  {lift:+.1f} pp (p={p:.3f})"
    ax.text(max(lift, 0) + 0.15, i, tag, va="center", fontsize=8.5)
ax.set(
    xlabel="KYC completion lift, pp",
    ylabel="Segment",
    title="Heterogeneous treatment effect by segment\n"
    "35\u201344 and Android respond; 45+ is flat (p=0.63)",
)
ax.legend(frameon=False, loc="lower right")
save(fig, "fig4_hte_lift.png")

# ── Fig 5: weekly first_tx flow vs behaviour ─────────────────────────────────
fun["week"] = pd.to_datetime(fun["install_date"]).dt.to_period("W").dt.start_time
wk = fun.groupby("week").agg(flow=("first_tx", "size"), conversions=("first_tx", "sum"))
wk["per_unit"] = wk["conversions"] / wk["flow"]
fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
ax.bar(wk.index, wk["flow"], width=4, color=MUTED, alpha=0.55, label="Installs (flow)")
ax.set(xlabel="Install week (2024)", ylabel="Installs", title="Weekly installs and first-tx rate")
ax2 = ax.twinx()
ax2.plot(
    wk.index, wk["per_unit"], marker="o", color=ACCENT, lw=2.2, label="First-tx rate (behaviour)"
)
for xi, yi in zip(wk.index, wk["per_unit"], strict=True):
    ax2.annotate(
        f"{yi:.1%}",
        (xi, yi),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center",
        fontsize=9,
        color=ACCENT,
    )
ax2.set_ylabel("First-tx rate per install", color=ACCENT)
ax2.set_ylim(0, 0.20)
ax.set_ylim(0, 3200)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="lower left")
ax.set_title("Weekly flow vs behaviour \u2014 rate stable ~12\u201314%, no \u00b130% swing")
save(fig, "fig5_weekly_trend.png")

# ── Fig 6: cohort retention heatmap ──────────────────────────────────────────
months = [f"month_{i}" for i in range(12)]
mat = coh.set_index("cohort")[months]
mat.columns = [f"M{i}" for i in range(12)]
fig, ax = plt.subplots(figsize=(11, 5.5), layout="constrained")
im = ax.imshow(mat.values, cmap="viridis", aspect="auto", vmin=0, vmax=0.7)
ax.set_xticks(range(len(mat.columns)))
ax.set_xticklabels(mat.columns, fontsize=9)
ax.set_yticks(range(len(mat.index)))
ax.set_yticklabels(mat.index, fontsize=9)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat.values[i, j]
        ax.text(
            j,
            i,
            f"{v:.0%}",
            ha="center",
            va="center",
            fontsize=6.5,
            color="white" if v < 0.42 else "black",
        )
ax.set(
    xlabel="Months since signup",
    ylabel="Signup cohort",
    title="Cohort retention \u2014 post-fix cohorts (from 2024-09) retain ~+12pp at M1",
)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("Retention share")
save(fig, "fig6_cohort_retention.png")

print("done")
