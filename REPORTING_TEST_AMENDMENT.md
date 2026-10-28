# Reporting and test amendment for C1 v2

This is an additive, local-only reporting and regression-test amendment. No new experiment was run. The frozen v2 protocol, evaluator, original v2 report, raw 1,200-trial JSON, freeze record, and original v2 ZIP remain unchanged.

## Correct-command result shown first

The most adverse tested correct-command condition is within-tolerance colluding: 38/160 (23.8%), with a 95% paired-seed-cluster bootstrap interval of 18.1–30.0% across 40 seed clusters. This result appears before the zero-event tables in the amended report.

## Zero-event reporting

The amendment derives summaries directly from the preserved `end_to_end_evaluation_v2.json` (SHA-256 `8363362e3a84b4acda5936e2b92957659e831cbe16b8a0de62972aa4dd14a3e9`). It reports the exact number of trial opportunities separately from the fraction of 40 independent seed clusters with one or more events. The latter receives a two-sided 95% exact Clopper–Pearson binomial interval; it is a cluster-incidence interval, not a per-trial risk interval.

For each membrane condition, action when no command is expected is 0/80 trials and 0/40 seed clusters with any action; each of the two individual probe-family cells is 0/40 trials and 0/40 clusters. Wrong command on valid probes is a separate endpoint: 0/320 trials and 0/40 clusters with any wrong command per condition. In each case the exact cluster interval is 0.0–8.8%. The pooled cross-condition totals (0/240 no-command trials and 0/960 valid-probe wrong-command trials) are labeled sensitivity summaries only because the three membrane conditions are distinct estimands; the pooled trial counts are not the independent denominator.

The omitted beyond-tolerance false-refusal endpoint is now included: 0/160 valid forward/reverse trials, with four directional opportunities per seed and 0/40 clusters with one or more false refusals. Its two-sided exact 95% Clopper–Pearson interval for cluster incidence is 0.0–8.8% (unrounded upper bound 0.088097); this is not a per-trial risk interval. The original paired-seed-cluster bootstrap remains degenerate at 0.0–0.0% for this all-zero outcome and is not used as a substitute.

## Regression added

`tests/test_c1_none_classifier_regression.py` first moves the actuator forward, then calls `apply_classifier(..., lambda: None)`. It verifies malformed-output classification, fail-closed `no_command`, zero drive/displacement, and reset position despite prior motion. This new test is outside the frozen v2 test-hash set.

The reporting utility and its tests are separate additive files: `reporting_amendment_v2.py`, `tests/test_reporting_amendment_v2.py`, `end_to_end_reporting_amendment_v2.json`, and `end_to_end_report_v2_reporting_amendment.md`. The reporting regression now checks the 0/160 endpoint, zero event clusters out of 40, the exact cluster interval, all four opportunities per seed, and explicit reporting of the bootstrap degeneracy.

## Verification

The full available regression set passed: 32 top-level Python tests, 10 original propulsion tests, and 15 JavaScript tests (57 total); all 10 reporting-amendment tests passed. `python3 evaluate_c1_e2e_v2.py --validate-only` passed and verified all original frozen hashes. After packaging, `unzip -t` passed for the new clean ZIP. SHA-256 comparison confirmed the frozen v2 files, raw trial JSON, earlier amended folder and archives, and original v2 archive remained unchanged; the original v2 ZIP SHA-256 remains `1a2172479c60bbf83f2bc79c52800c8477694b91cba3ac35fc2826d122e3f4cf`. No commit, push, or publication was performed.
