# C1 v2 reporting and regression-test amendment

This is an additive post-hoc presentation and test amendment. The frozen v2 protocol, evaluator, raw trial JSON, freeze record, and original v2 report are preserved unchanged; no new experiment was run.

**Worst tested correct-command result:** Within-tolerance colluding — **38/160 (23.8%)**, with a 95% paired-seed-cluster bootstrap interval of **18.1%–30.0%** across 40 seed clusters.

## Primary zero-event estimates by condition

Trial counts below are exact observed opportunity denominators. Separately, the interval is for the fraction of 40 independent seed clusters with at least one event in that condition’s stated opportunity set. Each cluster contributes two no-command trials or eight valid-probe trials; do not treat trial opportunities as independent clusters.

### Action when no command is expected

| Condition | Observed actions / tested trials | Seed clusters with ≥1 action | Two-sided 95% exact binomial interval for cluster fraction |
|---|---:|---:|---:|
| Clean | 0/80 | 0/40 | 0.0%–8.8% |
| Within-tolerance colluding | 0/80 | 0/40 | 0.0%–8.8% |
| Beyond-tolerance colluding | 0/80 | 0/40 | 0.0%–8.8% |

Each individual condition-by-probe-family cell is also shown separately; the two probe types remain distinguishable.

| Condition | Probe family | Observed actions / tested trials | Seed clusters with ≥1 action | Two-sided 95% exact binomial interval |
|---|---|---:|---:|---:|
| Clean | unfamiliar_random | 0/40 | 0/40 | 0.0%–8.8% |
| Clean | no_command | 0/40 | 0/40 | 0.0%–8.8% |
| Within-tolerance colluding | unfamiliar_random | 0/40 | 0/40 | 0.0%–8.8% |
| Within-tolerance colluding | no_command | 0/40 | 0/40 | 0.0%–8.8% |
| Beyond-tolerance colluding | unfamiliar_random | 0/40 | 0/40 | 0.0%–8.8% |
| Beyond-tolerance colluding | no_command | 0/40 | 0/40 | 0.0%–8.8% |

### Wrong command on valid probes

This is a distinct event definition from action on an unfamiliar or absent command. Each condition includes eight valid probe families per seed (four classes × clean/noisy), hence 320 trials but still only 40 independent seed clusters.

| Condition | Wrong commands / valid trials | Seed clusters with ≥1 wrong command | Two-sided 95% exact binomial interval for cluster fraction |
|---|---:|---:|---:|
| Clean | 0/320 | 0/40 | 0.0%–8.8% |
| Within-tolerance colluding | 0/320 | 0/40 | 0.0%–8.8% |
| Beyond-tolerance colluding | 0/320 | 0/40 | 0.0%–8.8% |

### False refusal on valid directional probes

Under the original v2 scoring rule, false refusal means a valid forward/reverse probe produced no movement. The beyond-tolerance condition has four such opportunities per seed (two directions × clean/noisy), for 160 observed trials across 40 independent seed clusters. The interval below is for the fraction of clusters with at least one false refusal, not per-trial risk.

| Condition | False refusals / valid directional trials | Seed clusters with ≥1 false refusal | Two-sided 95% exact binomial interval for cluster fraction |
|---|---:|---:|---:|
| Beyond-tolerance colluding | 0/160 | 0/40 | 0.0%–8.8% |

The original paired-seed-cluster bootstrap interval for this all-zero endpoint is degenerate at 0.0–0.0%; it is not substituted for the exact cluster-incidence interval above.

## Cross-condition sensitivity summaries

The membrane conditions are distinct estimands, so these pooled totals are supplementary only; the condition-specific results above are primary. A seed contributes six no-command opportunities across conditions and 24 valid-probe opportunities across conditions.

| Event definition | Observed events / tested trials | Seed clusters with ≥1 event | Two-sided 95% exact binomial interval for cluster fraction |
|---|---:|---:|---:|
| Action when no command is expected, all conditions | 0/240 | 0/40 | 0.0%–8.8% |
| Wrong command on valid probes, all conditions | 0/960 | 0/40 | 0.0%–8.8% |

A zero-event exact interval of 0.0–8.8% reflects uncertainty in the fraction of seed clusters with one or more events; it is not a per-trial risk interval. Zero observed events do not establish zero risk. The original paired-cluster bootstrap is degenerate at 0.0–0.0% for all-zero outcomes and is not a substitute for this finite-sample cluster-incidence interval.

Source v2 data SHA-256: `8363362e3a84b4acda5936e2b92957659e831cbe16b8a0de62972aa4dd14a3e9`. The machine-readable derivation is in [`end_to_end_reporting_amendment_v2.json`](end_to_end_reporting_amendment_v2.json); the generating utility is [`reporting_amendment_v2.py`](reporting_amendment_v2.py).

This is a selected synthetic software experiment, not safety validation, and makes no real-world performance claim.
