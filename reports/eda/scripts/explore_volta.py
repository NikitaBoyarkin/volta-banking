"""Volta EDA — precise recomputation of headline claims (wave 2, flagship).

Run with the shared EDA venv:
    /Users/nikitaboarkin/Desktop/00 ide/00 portfolio/.eda-tools/.venv/bin/python \
        reports/eda/scripts/explore_volta.py

Prints, as plain text, every number used in the report so each is reproducible.
No file writes; no project source touched.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (centre - half, centre + half)


def rule(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


# ── 1. Primary: onboarding funnel ────────────────────────────────────────────
rule("1. FUNNEL (data/charts/funnel.csv)")
fun = pd.read_csv(DATA / "charts" / "funnel.csv")
steps = ["app_install", "registration", "kyc_start", "kyc_complete", "card_ordered", "first_tx"]
print(f"rows={len(fun)}  users unique={fun['user_id'].nunique()}  dups={fun.duplicated().sum()}")
counts = {s: int(fun[s].sum()) for s in steps}
print("counts:", counts)
print(
    f"first_tx reach = {counts['first_tx']} / {counts['app_install']} = "
    f"{counts['first_tx'] / counts['app_install']:.4f}"
)
lo, hi = wilson(counts["first_tx"], counts["app_install"])
print(f"first_tx Wilson 95% CI = [{lo:.4f}, {hi:.4f}]")

print("\nstep-over-step conversion (parent -> child):")
for a, b in zip(steps[:-1], steps[1:], strict=True):
    conv = counts[b] / counts[a]
    lo, hi = wilson(counts[b], counts[a])
    print(f"  {a:>13} -> {b:<13} = {conv:6.2%}  CI [{lo:.3%}, {hi:.3%}]  drop {1 - conv:6.2%}")
print(f"\nkyc_complete as share of installs = {counts['kyc_complete'] / len(fun):.4f}")

# monotonic sanity
mono = all(counts[steps[i]] >= counts[steps[i + 1]] for i in range(len(steps) - 1))
print(f"monotone non-increasing across steps: {mono}")

print("\nmetric first_tx by segment:")
for col in ("channel", "device", "age_group"):
    g = fun.groupby(col)["first_tx"].agg(["count", "sum", "mean"]).sort_values("mean")
    g["share"] = g["sum"] / g["sum"].sum()
    print(f"\n[{col}]")
    print(g.to_string())
    print(f"  max/min gap = {g['mean'].max() / g['mean'].min():.3f}")

print("\nweekly first_tx (flow vs behaviour):")
fun["install_week"] = pd.to_datetime(fun["install_date"]).dt.to_period("W").dt.start_time
wk = fun.groupby("install_week").agg(value=("first_tx", "sum"), count=("first_tx", "size"))
wk["per_unit"] = wk["value"] / wk["count"]
print(wk.to_string())

# validity: first_tx_date present iff first_tx == 1
has_date = fun["first_tx_date"].notna()
consistent = (has_date == (fun["first_tx"] == 1)).all()
print(f"\nfirst_tx_date present iff first_tx==1: {consistent}")
# install dates range
idates = pd.to_datetime(fun["install_date"])
print(f"install_date range: {idates.min()} .. {idates.max()}")
print(
    f"future install dates (>{pd.Timestamp('2026-10-13')}): {(idates > pd.Timestamp('2026-10-13')).sum()}"
)

# ── 2. A/B experiment ────────────────────────────────────────────────────────
rule("2. A/B EXPERIMENT (data/volta_ab_experiment.csv)")
ab = pd.read_csv(DATA / "volta_ab_experiment.csv")
print(f"rows={len(ab)}  dups={ab.duplicated().sum()}  nulls={int(ab.isna().sum().sum())}")
grp = ab.groupby("group")["kyc_completed"].agg(["count", "sum", "mean"])
print(grp.to_string())
c = ab[ab["group"] == "control"]["kyc_completed"].values
t = ab[ab["group"] == "treatment"]["kyc_completed"].values
cr, tr = c.mean(), t.mean()
lift = tr - cr
print(f"\ncontrol={cr:.6f}  treatment={tr:.6f}  abs lift={lift:.6f} ({lift * 100:.4f} pp)")

table = np.array([[t.sum(), len(t) - t.sum()], [c.sum(), len(c) - c.sum()]])
chi2, p, dof, _ = stats.chi2_contingency(table)
se = np.sqrt(cr * (1 - cr) / len(c) + tr * (1 - tr) / len(t))
z = lift / se
print(f"chi2={chi2:.4f}  dof={dof}  p={p:.3e}  z={z:.4f}")
# two-proportion z p
pz = 2 * stats.norm.sf(abs(z))
print(f"z-test two-sided p = {pz:.3e}")
lo, hi = lift - 1.96 * se, lift + 1.96 * se
print(f"normal-approx 95% CI for lift = [{lo * 100:.3f}pp, {hi * 100:.3f}pp]")

rng = np.random.default_rng(42)
tb = rng.choice(t, size=(2000, len(t))).mean(axis=1)
cb = rng.choice(c, size=(2000, len(c))).mean(axis=1)
bd = tb - cb
print(
    f"bootstrap 95% CI = [{np.percentile(bd, 2.5) * 100:.3f}pp, "
    f"{np.percentile(bd, 97.5) * 100:.3f}pp]"
)

# SRM
obs = np.array([len(c), len(t)])
chi2_srm, p_srm = stats.chisquare(obs, [obs.sum() / 2, obs.sum() / 2])
print(f"SRM chi2={chi2_srm:.4f} p={p_srm:.4f}")

# guardrails
for metric, _direction in (("churned_30d", "lower"), ("revenue_30d_eur", "higher")):
    cc = ab[ab["group"] == "control"][metric]
    tt = ab[ab["group"] == "treatment"][metric]
    ts, pv = stats.ttest_ind(tt, cc, equal_var=False)
    print(
        f"guardrail {metric}: control={cc.mean():.4f} treatment={tt.mean():.4f} "
        f"diff={tt.mean() - cc.mean():+.4f} welch_p={pv:.4f}"
    )

# CUPED variance reduction (rho^2 on control)

x = ab["pre_kyc_rate"].values
y = ab["kyc_completed"].values
ctrl_mask = (ab["group"] == "control").values
theta = np.cov(y[ctrl_mask], x[ctrl_mask])[0, 1] / np.var(x[ctrl_mask])
y_cuped = y - theta * x
var_red = (1 - np.var(y_cuped[ctrl_mask]) / np.var(y[ctrl_mask])) * 100
print(
    f"CUPED: theta={theta:.4f}  variance reduction={var_red:.2f}%  "
    f"rho^2={np.corrcoef(y[ctrl_mask], x[ctrl_mask])[0, 1] ** 2 * 100:.2f}%"
)

print("\nHTE by segment (raw two-proportion):")
for col in ("age_group", "device", "channel"):
    for val in sorted(ab[col].unique()):
        sub = ab[ab[col] == val]
        cc = sub[sub["group"] == "control"]["kyc_completed"].values
        tt = sub[sub["group"] == "treatment"]["kyc_completed"].values
        tb2 = np.array([[tt.sum(), len(tt) - tt.sum()], [cc.sum(), len(cc) - cc.sum()]])
        _, pv, _, _ = stats.chi2_contingency(tb2)
        print(
            f"  {col}={val:<12} n={len(sub):5d} ctrl={cc.mean():.4f} "
            f"trt={tt.mean():.4f} lift={(tt.mean() - cc.mean()) * 100:+.2f}pp p={pv:.4f}"
        )

# ── 3. Business impact reproduction ──────────────────────────────────────────
rule("3. BUSINESS IMPACT (+656K / 44x ROI)")
ltv = 85
installs = 50_000
kyc_start_conv = 0.492
card_rate = 0.718
tx_rate = 0.637
kyc_starters = installs * kyc_start_conv
add_completions = kyc_starters * lift
add_activated = add_completions * card_rate * tx_rate
monthly_rev = add_activated * ltv
annual = monthly_rev * 12
roi = annual / 15_000
print(f"monthly_kyc_starters        = {kyc_starters:,.1f}")
print(f"additional_kyc_completions  = {add_completions:,.2f}")
print(f"additional_activated        = {add_activated:,.2f}")
print(f"additional_monthly_revenue  = EUR {monthly_rev:,.2f}")
print(f"additional_annual_revenue   = EUR {annual:,.2f}")
print(f"ROI multiple                = {roi:.2f}x")
# funnel-derived equivalents
print(
    f"\nfunnel card_rate (card/kyc_complete) = {counts['card_ordered'] / counts['kyc_complete']:.4f}"
)
print(f"funnel tx_rate (first_tx/card)       = {counts['first_tx'] / counts['card_ordered']:.4f}")
print(f"funnel kyc_start/installs            = {counts['kyc_start'] / len(fun):.4f}")

# ── 4. Supporting datasets ───────────────────────────────────────────────────
rule("4. SUPPORTING DATASETS")
seg = pd.read_csv(DATA / "segment_profiles.csv")
print("segment_profiles:")
print(seg.to_string(index=False))
print(
    f"  revenue share sums to {seg['revenue_share'].sum():.1f}%; "
    f"Power share={seg.loc[0, 'revenue_share']}% on "
    f"{seg.loc[0, 'n_users'] / seg['n_users'].sum():.1%} of users"
)
print(
    f"  top-2 users share = {(seg['n_users'].head(2).sum() / seg['n_users'].sum()):.1%}, "
    f"top-2 revenue share = {seg['revenue_share'].head(2).sum():.1f}%"
)

coh = pd.read_csv(DATA / "cohort_retention_matrix.csv")
print("\ncohort_retention_matrix: cols", list(coh.columns)[:4], "...")
print(f"  cohorts={len(coh)}  size range [{coh['cohort_size'].min()}, {coh['cohort_size'].max()}]")
print(
    f"  M1 mean={coh['month_1'].mean():.4f}  M3 mean={coh['month_3'].mean():.4f}  "
    f"M6 mean={coh['month_6'].mean():.4f}"
)
# pre vs post fix (2024-09)
pre = coh[coh["cohort"] < "2024-09"]
post = coh[coh["cohort"] >= "2024-09"]
for m in ("month_1", "month_3"):
    ts, pv = stats.ttest_ind(post[m], pre[m], equal_var=False)
    print(
        f"  {m}: pre={pre[m].mean():.4f} post={post[m].mean():.4f} "
        f"delta={(post[m].mean() - pre[m].mean()) * 100:+.2f}pp welch_p={pv:.4f}"
    )

anc = pd.read_csv(DATA / "volta_anchor_cac.csv")
print("\nanchor_cac:")
print(f"  rows={len(anc)}  channels={anc['channel'].unique().tolist()}")
print(f"  users total={anc['users'].sum():,}")
print(
    f"  marginal_cac range [{anc['marginal_cac_eur'].min():.2f}, {anc['marginal_cac_eur'].max():.2f}]"
)
print(f"  ltv range [{anc['ltv_eur'].min():.2f}, {anc['ltv_eur'].max():.2f}]")
anc["ltv_cac"] = anc["ltv_eur"] / anc["marginal_cac_eur"]
print(f"  ltv/cac range [{anc['ltv_cac'].min():.2f}, {anc['ltv_cac'].max():.2f}]")
# blended as scale grows
anc_sorted = anc.sort_values("bucket_id")
cum = anc_sorted.assign(cum_users=anc_sorted["users"].cumsum())
blended = (cum["ltv_eur"] * cum["users"]).cumsum() / (
    cum["marginal_cac_eur"] * cum["users"]
).cumsum()
print(f"  blended LTV/CAC last bucket = {blended.iloc[-1]:.3f}")
for thr in (70_000, 225_000):
    idx = cum[cum["cum_users"] >= thr]
    if len(idx):
        i = idx.index[0]
        print(f"  blended LTV/CAC at {thr:,} users = {blended.loc[i]:.3f}")

# ── 5. Cross-file duplication check ──────────────────────────────────────────
rule("5. FUNNEL FILE DUPLICATION CHECK")
alt = DATA / "volta_funnel_data.csv"
if alt.exists():
    alt_df = pd.read_csv(alt)
    print(f"charts/funnel.csv  shape={fun.shape} cols={list(fun.columns)}")
    print(f"volta_funnel_data  shape={alt_df.shape} cols={list(alt_df.columns)}")
    common_cols = [c for c in fun.columns if c in alt_df.columns]
    print(f"common cols={common_cols}")
    if len(alt_df) == len(fun):
        same = (
            (
                fun[common_cols].reset_index(drop=True).fillna(-999)
                == alt_df[common_cols].reset_index(drop=True).fillna(-999)
            )
            .all()
            .all()
        )
        print(f"identical on common cols: {same}")
