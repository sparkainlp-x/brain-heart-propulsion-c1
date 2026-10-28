# C1 end-to-end evaluation — corrected frozen protocol v2

> **V1 per-class end-to-end rates are superseded by a pairing bug.** The v1 evaluator used fixed episode-index pairing that aliased some membrane episodes to probe families. V1 files remain preserved for audit, but its per-class rates should not be interpreted. The corrected v2 results below use a seed-specific shuffled episode-to-family assignment reused across conditions.

This is a selected synthetic software experiment, **not safety validation**. The membrane model and classifier receive separate generated inputs. Expected labels are attached only after the resettable, label-blind gate and simulated ring action, for scoring only.

- Protocol SHA-256: `54a3845ba688ddf68461a89398fb85f4f0dd289666935ecfd649da22933209de`
- Evaluator SHA-256: `43065b3ee988e0df1467793a23a668c5cd0e40646b53e241c44d568b26e5ca69`
- Protocol frozen before data: 2026-10-28T01:48:55.574087+00:00
- Evaluation generated: 2026-10-28T01:49:11.998814+00:00
- Design: 40 paired seed clusters × 3 membrane conditions × 10 probe families = **1,200 trials**. One shuffled episode-to-family assignment is reused across the three conditions within each seed.
- Frozen classifier calibration: tau 0.257; Youden J 0.990.

**Worst tested correct-command condition:** within-tolerance colluding, **38/160 (23.8%)**, with a 95% paired-seed-cluster bootstrap interval of **18.1–30.0%** (40 seed clusters).

## Valid-command outcomes

These rates concern valid forward/reverse probes, plus wrong-command outcomes across all four valid classes. A false refusal is a valid forward/reverse probe that produced no motion; hold/rest with no motion is correct.

| Membrane condition | Correct forward/reverse command | False refusal on valid directional probe | Wrong command on valid probes |
|---|---:|---:|---:|
| Clean | 84/160 (52.5%; paired-seed 95% bootstrap 46.2–59.4%) | 76/160 (47.5%; 40.6–53.8%) | 0/320 (paired-seed 95% bootstrap 0.0–0.0%) |
| Within-tolerance colluding | **38/160 (23.8%; paired-seed 95% bootstrap 18.1–30.0%)** | 122/160 (76.2%; 70.0–81.9%) | 0/320 (paired-seed 95% bootstrap 0.0–0.0%) |
| Beyond-tolerance colluding | 160/160 (100.0%; paired-seed 95% bootstrap 100.0–100.0%) | 0/160 (paired-seed 95% bootstrap 0.0–0.0%) | 0/320 (paired-seed 95% bootstrap 0.0–0.0%) |

## Unfamiliar and absent-command outcomes

These are separate no-command cases: the classifier receives either an unfamiliar random probe or no command input. Each cell below is one trial per seed in 40 independent seed clusters.

| Membrane condition | Action on unfamiliar input | Action on absent command |
|---|---:|---:|
| Clean | **0/40** (paired-seed bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) | **0/40** (paired-seed bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) |
| Within-tolerance colluding | **0/40** (paired-seed bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) | **0/40** (paired-seed bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) |
| Beyond-tolerance colluding | **0/40** (paired-seed bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) | **0/40** (paired-seed bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) |

For every no-command cell, the exact observed count is **0/40** and the per-cell 95% Wilson upper bound is **8.8%**. The paired bootstrap interval is degenerate because every resampled seed cluster also had zero actions. **0 observed is not zero risk.**

## Per-class classifier confusion and action outcomes

`F/R/H/Rest/X` are classifier predictions `forward/reverse/hold/rest/reject`. Each prediction count is out of 40 seed clusters. `Correct cmd` applies to forward/reverse; `Correct none` applies to hold/rest. Every `0/40†` is an observed zero, not proof of zero risk.

| Condition | Probe quality | Target | F | R | H | Rest | X | Correct cmd | Correct none | Wrong cmd | False refusal |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| clean | clean | forward | 40/40 | 0/40† | 0/40† | 0/40† | 0/40† | 24/40 | — | 0/40† | 16/40 |
| clean | clean | reverse | 0/40† | 40/40 | 0/40† | 0/40† | 0/40† | 16/40 | — | 0/40† | 24/40 |
| clean | clean | hold | 0/40† | 0/40† | 40/40 | 0/40† | 0/40† | — | 40/40 | 0/40† | — |
| clean | clean | rest | 0/40† | 0/40† | 0/40† | 40/40 | 0/40† | — | 40/40 | 0/40† | — |
| clean | noisy_sigma_0.15 | forward | 40/40 | 0/40† | 0/40† | 0/40† | 0/40† | 20/40 | — | 0/40† | 20/40 |
| clean | noisy_sigma_0.15 | reverse | 0/40† | 40/40 | 0/40† | 0/40† | 0/40† | 24/40 | — | 0/40† | 16/40 |
| clean | noisy_sigma_0.15 | hold | 0/40† | 0/40† | 40/40 | 0/40† | 0/40† | — | 40/40 | 0/40† | — |
| clean | noisy_sigma_0.15 | rest | 0/40† | 0/40† | 0/40† | 40/40 | 0/40† | — | 40/40 | 0/40† | — |
| within_tolerance_colluding | clean | forward | 40/40 | 0/40† | 0/40† | 0/40† | 0/40† | 7/40 | — | 0/40† | 33/40 |
| within_tolerance_colluding | clean | reverse | 0/40† | 40/40 | 0/40† | 0/40† | 0/40† | 8/40 | — | 0/40† | 32/40 |
| within_tolerance_colluding | clean | hold | 0/40† | 0/40† | 40/40 | 0/40† | 0/40† | — | 40/40 | 0/40† | — |
| within_tolerance_colluding | clean | rest | 0/40† | 0/40† | 0/40† | 40/40 | 0/40† | — | 40/40 | 0/40† | — |
| within_tolerance_colluding | noisy_sigma_0.15 | forward | 40/40 | 0/40† | 0/40† | 0/40† | 0/40† | 11/40 | — | 0/40† | 29/40 |
| within_tolerance_colluding | noisy_sigma_0.15 | reverse | 0/40† | 40/40 | 0/40† | 0/40† | 0/40† | 12/40 | — | 0/40† | 28/40 |
| within_tolerance_colluding | noisy_sigma_0.15 | hold | 0/40† | 0/40† | 40/40 | 0/40† | 0/40† | — | 40/40 | 0/40† | — |
| within_tolerance_colluding | noisy_sigma_0.15 | rest | 0/40† | 0/40† | 0/40† | 40/40 | 0/40† | — | 40/40 | 0/40† | — |
| beyond_tolerance_colluding | clean | forward | 40/40 | 0/40† | 0/40† | 0/40† | 0/40† | 40/40 | — | 0/40† | 0/40† |
| beyond_tolerance_colluding | clean | reverse | 0/40† | 40/40 | 0/40† | 0/40† | 0/40† | 40/40 | — | 0/40† | 0/40† |
| beyond_tolerance_colluding | clean | hold | 0/40† | 0/40† | 40/40 | 0/40† | 0/40† | — | 40/40 | 0/40† | — |
| beyond_tolerance_colluding | clean | rest | 0/40† | 0/40† | 0/40† | 40/40 | 0/40† | — | 40/40 | 0/40† | — |
| beyond_tolerance_colluding | noisy_sigma_0.15 | forward | 40/40 | 0/40† | 0/40† | 0/40† | 0/40† | 40/40 | — | 0/40† | 0/40† |
| beyond_tolerance_colluding | noisy_sigma_0.15 | reverse | 0/40† | 40/40 | 0/40† | 0/40† | 0/40† | 40/40 | — | 0/40† | 0/40† |
| beyond_tolerance_colluding | noisy_sigma_0.15 | hold | 0/40† | 0/40† | 40/40 | 0/40† | 0/40† | — | 40/40 | 0/40† | — |
| beyond_tolerance_colluding | noisy_sigma_0.15 | rest | 0/40† | 0/40† | 0/40† | 40/40 | 0/40† | — | 40/40 | 0/40† | — |

† Each 0/40 cell has a 95% Wilson interval of 0.0–8.8%; 0 observed does not mean zero risk. Pooled rates use 2,000 fixed bootstrap replicates of whole seed clusters, preserving the paired design. The JSON also includes per-class confidence intervals, per-seed cluster counts, classifier exceptions, and all 1,200 raw trial records.

## Interpretation boundary

The red collusion panel in the supplied diagram and prior `EVALUATION.md` are membrane-permission-stage-only fault tests; they are not end-to-end action rates. The v2 batch helper returns membrane event bits only, never planted/truth labels. Each trial resets drive, position, phases, and clock; rejected, unknown, malformed, missing, or exceptional classifier output maps to `no_command`.

This is a selected synthetic generated-input experiment, **not safety validation**. It makes no safety, robustness, biological, medical, hardware, or real-world performance claim. The brain and heart terms are metaphors only; there is no neural/ECG signal or physical actuator.

See [`END_TO_END_PROTOCOL_V2.md`](END_TO_END_PROTOCOL_V2.md), [`end_to_end_evaluation_v2.json`](end_to_end_evaluation_v2.json), the superseded v1 report [`end_to_end_report.md`](end_to_end_report.md) (audit only), and the separate membrane-only [`EVALUATION.md`](EVALUATION.md).
