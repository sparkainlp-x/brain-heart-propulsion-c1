# C1 end-to-end evaluation (frozen protocol v1)

This is a separate full-chain evaluation; the earlier `evaluation.json` remains membrane-stage only. The membrane model and classifier receive separate generated inputs. Target labels are attached only after the resettable, label-blind gate and simulated ring action for scoring.

- Protocol SHA-256: `658e1c2d724ec32370ffa7c9ba91010fe7d3b33ebe0d037b6cb57bc1950dd7f8`
- Evaluator SHA-256: `d9294c93426a4e649263ee20e6e70396d4bdd7092f29d78583f8bd1d85eeeb94`
- Protocol frozen at: 2026-10-28T01:45:15.713889+00:00
- Evaluation generated at: 2026-10-28T01:45:27.247003+00:00
- Design: 40 paired seed clusters × 3 membrane conditions × 10 probe families = 1200 trials.
- Frozen classifier calibration: tau 0.257; Youden J 0.990.

## Distinct end-to-end outcomes

Correct command, wrong command, action when no command is expected, and false refusal are separate measures. False refusal applies to valid forward/reverse probes that result in no movement. For hold/rest, no movement is correct; classifier misrecognition and unexpected movement are reported separately.

| Membrane condition | Correct command on valid forward/reverse | Wrong command on all valid probes | False refusal on valid directional probes | Action on unfamiliar input (no command expected) | Action on absent command |
|---|---:|---:|---:|---:|---:|
| Clean | 80/160 (50.0%; 95% seed-cluster bootstrap 50.0–50.0%) | 0/320 (0.0%; 95% seed-cluster bootstrap 0.0–0.0%) | 80/160 (50.0%; 95% seed-cluster bootstrap 50.0–50.0%) | 0/40 (0.0%; 95% seed Wilson 0.0–8.8%) | 0/40 (0.0%; 95% seed Wilson 0.0–8.8%) |
| Within-tolerance colluding | 43/160 (26.9%; 95% seed-cluster bootstrap 21.9–31.9%) | 0/320 (0.0%; 95% seed-cluster bootstrap 0.0–0.0%) | 117/160 (73.1%; 95% seed-cluster bootstrap 68.1–78.1%) | 0/40 (0.0%; 95% seed Wilson 0.0–8.8%) | 0/40 (0.0%; 95% seed Wilson 0.0–8.8%) |
| Beyond-tolerance colluding | 159/160 (99.4%; 95% seed-cluster bootstrap 98.1–100.0%) | 0/320 (0.0%; 95% seed-cluster bootstrap 0.0–0.0%) | 1/160 (0.6%; 95% seed-cluster bootstrap 0.0–1.9%) | 0/40 (0.0%; 95% seed Wilson 0.0–8.8%) | 0/40 (0.0%; 95% seed Wilson 0.0–8.8%) |

Pooled intervals resample entire paired seed clusters (2,000 fixed bootstrap replicates). Single-cell rates also include Wilson intervals based on 40 independent seeds; zero observations therefore retain a nonzero upper bound.

## Per-class classifier confusion and end-to-end outcomes

`F/R/H/Rest/X` are classifier predictions `forward/reverse/hold/rest/reject`; each cell is out of 40 independent seed clusters. `Correct cmd` applies to forward/reverse; `Correct none` applies to hold/rest.

| Condition | Probe quality | Target | F | R | H | Rest | X | Correct cmd | Correct none | Wrong cmd | False refusal |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| clean | clean | forward | 40 | 0 | 0 | 0 | 0 | 40/40 | — | 0/40 | 0/40 |
| clean | clean | reverse | 0 | 40 | 0 | 0 | 0 | 0/40 | — | 0/40 | 40/40 |
| clean | clean | hold | 0 | 0 | 40 | 0 | 0 | — | 40/40 | 0/40 | — |
| clean | clean | rest | 0 | 0 | 0 | 40 | 0 | — | 40/40 | 0/40 | — |
| clean | noisy_sigma_0.15 | forward | 40 | 0 | 0 | 0 | 0 | 40/40 | — | 0/40 | 0/40 |
| clean | noisy_sigma_0.15 | reverse | 0 | 39 | 0 | 0 | 1 | 0/40 | — | 0/40 | 40/40 |
| clean | noisy_sigma_0.15 | hold | 0 | 0 | 39 | 0 | 1 | — | 40/40 | 0/40 | — |
| clean | noisy_sigma_0.15 | rest | 0 | 0 | 0 | 39 | 1 | — | 40/40 | 0/40 | — |
| within_tolerance_colluding | clean | forward | 40 | 0 | 0 | 0 | 0 | 21/40 | — | 0/40 | 19/40 |
| within_tolerance_colluding | clean | reverse | 0 | 40 | 0 | 0 | 0 | 0/40 | — | 0/40 | 40/40 |
| within_tolerance_colluding | clean | hold | 0 | 0 | 40 | 0 | 0 | — | 40/40 | 0/40 | — |
| within_tolerance_colluding | clean | rest | 0 | 0 | 0 | 40 | 0 | — | 40/40 | 0/40 | — |
| within_tolerance_colluding | noisy_sigma_0.15 | forward | 40 | 0 | 0 | 0 | 0 | 22/40 | — | 0/40 | 18/40 |
| within_tolerance_colluding | noisy_sigma_0.15 | reverse | 0 | 39 | 0 | 0 | 1 | 0/40 | — | 0/40 | 40/40 |
| within_tolerance_colluding | noisy_sigma_0.15 | hold | 0 | 0 | 39 | 0 | 1 | — | 40/40 | 0/40 | — |
| within_tolerance_colluding | noisy_sigma_0.15 | rest | 0 | 0 | 0 | 39 | 1 | — | 40/40 | 0/40 | — |
| beyond_tolerance_colluding | clean | forward | 40 | 0 | 0 | 0 | 0 | 40/40 | — | 0/40 | 0/40 |
| beyond_tolerance_colluding | clean | reverse | 0 | 40 | 0 | 0 | 0 | 40/40 | — | 0/40 | 0/40 |
| beyond_tolerance_colluding | clean | hold | 0 | 0 | 40 | 0 | 0 | — | 40/40 | 0/40 | — |
| beyond_tolerance_colluding | clean | rest | 0 | 0 | 0 | 40 | 0 | — | 40/40 | 0/40 | — |
| beyond_tolerance_colluding | noisy_sigma_0.15 | forward | 40 | 0 | 0 | 0 | 0 | 40/40 | — | 0/40 | 0/40 |
| beyond_tolerance_colluding | noisy_sigma_0.15 | reverse | 0 | 39 | 0 | 0 | 1 | 39/40 | — | 0/40 | 1/40 |
| beyond_tolerance_colluding | noisy_sigma_0.15 | hold | 0 | 0 | 39 | 0 | 1 | — | 40/40 | 0/40 | — |
| beyond_tolerance_colluding | noisy_sigma_0.15 | rest | 0 | 0 | 0 | 39 | 1 | — | 40/40 | 0/40 | — |

The JSON also includes per-class confidence intervals, per-seed cluster counts, classifier exceptions, and all 1,200 raw trial records.

## Interpretation boundary

The red panel in the supplied diagram and the prior `EVALUATION.md` are membrane-only fault-test results; they are not end-to-end action rates. This report scores the separate combined gate through the in-memory clock and ring. The batch helper returns membrane event bits only, never planted/truth labels. Each trial resets drive, position, phases, and clock; rejected, unknown, malformed, missing, or exceptional classifier output maps to `no_command`.

This is only a selected generated-input software-model evaluation. It makes no safety, robustness, biological, medical, hardware, or real-world performance claim. The diagram continues to label the logic as not a safety guarantee.

See [`END_TO_END_PROTOCOL.md`](END_TO_END_PROTOCOL.md), [`end_to_end_evaluation.json`](end_to_end_evaluation.json), and the separate prior [`EVALUATION.md`](EVALUATION.md).
