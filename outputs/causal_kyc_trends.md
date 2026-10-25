======================================================================
VOLTA NEOBANK — CAUSAL LAYER (REQ-201, Portfolio 2.0)
======================================================================

Dataset shape:   (84000, 12)
Users:           84,000
Cohorts:         24 (2023-01 .. 2024-12)
Cutoff:          2024-09  (post = 14,000 users)

Design — difference-in-differences:
  treated    = in-app KYC flow    (subject to the progress-bar fix)
  comparison = partner KYC flow    (agent-assisted; fix does not apply)

Flow sizes:
  in_app_kyc        50,400  (60.0%)
  partner_kyc       33,600  (40.0%)

======================================================================
NAIVE PRE/POST VS DIFFERENCE-IN-DIFFERENCES
======================================================================

The old Project-3 claim measured a pooled pre/post change (ignoring
the comparison group). The DiD nets out the shared time trend.

             naive_pre_post_pp  did_2x2_pp
outcome                                   
activated               6.2900      4.9900
retained_m1             7.5900      7.5700
retained_m3             7.6000      9.1600

----------------------------------------------------------------------
READING IT
----------------------------------------------------------------------
  activated    naive +6.29pp  →  DiD +4.99pp
  retained_m1  naive +7.59pp  →  DiD +7.57pp
  retained_m3  naive +7.60pp  →  DiD +9.16pp

======================================================================
COVARIATE-ADJUSTED DID (COHORT-CLUSTERED SE)
======================================================================

ATT = coefficient on treated × post; 95% CI uses t(G−1).

             ATT_pp  SE_pp  CI_low_pp  CI_high_pp      p
outcome                                                 
activated    4.9226 0.4103     4.0738      5.7714 0.0000
retained_m1  7.4852 0.7558     5.9218      9.0487 0.0000
retained_m3  9.0859 1.3905     6.2095     11.9624 0.0000

  Clusters (cohorts): 24   N: 84,000

  All three outcomes show a significant positive ATT consistent with
  the narrative chain: activation → M1 → M3 retention.

======================================================================
RECOVERY CHECK — DID VS THE KNOWN EFFECT
======================================================================

The generator injects a known total ATT, so a correctly specified
estimator should recover it. This is the methods demonstration.

             true_ATT_pp  recovered_ATT_pp  diff_pp CI_covers_truth
outcome                                                            
activated         5.7000            4.9230  -0.7770             yes
retained_m1       8.5000            7.4850  -1.0150             yes
retained_m3       9.0000            9.0860   0.0860             yes

  3/3 95% CIs cover the injected effect.
  → The estimator recovers the known effect within sampling error.

======================================================================
DIAGNOSTIC — PARALLEL TRENDS (PRE-PERIOD)
======================================================================

Slope of the (treated − comparison) retention gap over pre-period cohorts.
A slope indistinguishable from zero is consistent with parallel trends.

             gap_slope_pp_per_month      p     r2
outcome                                          
activated                    0.0255 0.6984 0.0085
retained_m1                 -0.0641 0.3555 0.0476
retained_m3                 -0.0607 0.2928 0.0613

  → No pre-trend detected (p > 0.05 on every outcome): the design is credible.

======================================================================
DIAGNOSTIC — PLACEBO TEST (fake cutoff 2024-01)
======================================================================

Re-run the DiD with a fake cutoff inside the pre-period. A real effect
should vanish; a significant estimate would signal a pre-trend or bias.

             placebo_ATT_pp  CI_low_pp  CI_high_pp      p CI_covers_0
outcome                                                              
activated            0.4978    -1.0219      2.0174 0.5013         yes
retained_m1         -0.8151    -2.5050      0.8749 0.3254         yes
retained_m3         -0.3353    -1.6717      1.0011 0.6056         yes

  → Placebo effect ~0 and every CI covers 0: the real DiD result holds.

======================================================================
DIAGNOSTIC — COVARIATE BALANCE (PRE-PERIOD SMD)
======================================================================

Standardized mean differences between treated and comparison flows.
The skill's gate blocks when max |SMD| >= 0.2.

     covariate     smd  abs_smd
       age=45+ -0.1570   0.1570
    device=web -0.1370   0.1370
    device=ios  0.1330   0.1330
     age=18-24  0.1220   0.1220
  pre_activity  0.1100   0.1100
     age=25-34  0.0890   0.0890
     age=35-44 -0.0280   0.0280
device=android  0.0230   0.0230

  Max |SMD| = 0.157  →  PASS (threshold 0.2)

======================================================================
DIAGNOSTIC — PROPENSITY OVERLAP
======================================================================

  PS range:            0.384 .. 0.798
  Common support:      [0.407, 0.788]
  Share in support:    100.0%

  → Substantial overlap: treated and comparison units are comparable.

======================================================================
TREND CHART
======================================================================

Saved: causal_kyc_trends.png

======================================================================
LIMITATION — READ BEFORE CITING
======================================================================

  The data is synthetic. `generate_causal_kyc_data.py` injects known TOTAL
  effects (+5.7pp activation, +8.5pp M1, +9.0pp M3), so the DiD recovering
  those values (within the 95% CI — see the recovery check above) demonstrates
  that:

    • the estimator is correctly specified and recovers a known effect,
    • parallel trends / placebo / balance / overlap diagnostics behave as
      they should.

  It is NOT evidence about a real bank. The value of this layer is the
  method and the diagnostic discipline, not the point estimate.


======================================================================
CONCLUSION — THE CLAIM SURVIVES A CAUSAL TEST
======================================================================

  Project 3 supported "the KYC fix drove retention" with a pre/post Welch
  t-test — a correlation. Re-analysed as difference-in-differences against a
  not-treated comparison flow:

    • the DiD ATT is positive and significant on activation, M1 and M3,
    • pre-period parallel trends hold (no differential drift),
    • the placebo test at a fake cutoff returns ~0,
    • covariates are balanced and propensity scores overlap.

  The narrative claim is not weakened by a causal test — it is upgraded from
  correlation to a design that would have caught a pre-trend if one existed.

======================================================================
Analysis complete.
======================================================================
