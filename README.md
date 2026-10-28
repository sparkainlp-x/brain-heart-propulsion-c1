# Brain–heart–propulsion C1 (software-only prototype)

This repository contains a software-only integration of the copied Membrane Arena synthetic brain simulator and the uploaded brain-heart-propulsion toy. The original upload and Membrane Arena repository remain unchanged; no code runs on a device.

## What is connected

C1 composes two separate synthetic stages. The membrane model emits or withholds a permission event. Separately, the propulsion toy's calibrated classifier evaluates its own generated probe and can return `forward`, `reverse`, `hold`, or `rest`. A known accepted response passes only when both the permission event and classifier acceptance are present. The classifier response supplies the toy drive direction; no signal is passed between the models.

Each trial clears command state and drive and resets ring position, phases, and the software clock. Rejected, unknown, malformed, missing, or exceptional classifier output becomes `no_command` with zero drive. If the permission event is absent, drive also remains zero. This is a literal software composition, not a unified brain model or scientific discovery. “Heart” means a software clock; “propulsion” means an in-memory phase ring.

## Post-hoc reporting and test amendment

**Worst tested correct-command result:** within-tolerance colluding, **38/160 (23.8%)**, with a 95% paired-seed-cluster bootstrap interval of **18.1–30.0%** across 40 seed clusters.

For pooled zero-event endpoints, the number of tested trials and the number of independent seed clusters answer different questions. Across the two no-command probe families within each condition, there were **0/80 actions** and **0/40 seed clusters with any action**; the two-sided 95% exact binomial interval for the cluster fraction is **0.0–8.8%**. Wrong commands on valid probes are a separate endpoint: **0/320 trials** and **0/40 seed clusters with any wrong command** per condition, also with a 0.0–8.8% exact cluster-level interval. The per-trial denominators are observed opportunity counts, not independent clusters; zero observed events do not establish zero risk.

The cross-condition `0/240` no-command total is included only as a sensitivity summary because the three membrane conditions are distinct estimands. The original v2 protocol, raw data, evaluator, freeze record, and `end_to_end_report_v2.md` remain unchanged. See [`end_to_end_report_v2_reporting_amendment.md`](end_to_end_report_v2_reporting_amendment.md) and its reproducible derivation [`reporting_amendment_v2.py`](reporting_amendment_v2.py).

## Corrected end-to-end test (v2)

> **V1 per-class end-to-end rates are superseded by a pairing bug.** The v1 fixed episode-index pairing aliased some membrane episodes with probe families. V1 files are retained for audit only; do not interpret their per-class rates. The corrected v2 results below use a seed-specific shuffled episode-to-family assignment reused across conditions.

This frozen experiment crosses three membrane conditions with four named classes in clean and noisy probes, an unfamiliar random probe, and an absent-command case. It uses separate generated membrane and classifier inputs, 40 paired seed clusters, and 1,200 total trials. Expected labels are used only for scoring after simulated actuation.

### Valid-command outcomes

| Membrane condition | Correct forward/reverse command | False refusal on valid directional probe | Wrong command on valid probes |
|---|---:|---:|---:|
| Clean | 84/160 (52.5%; paired-seed 95% bootstrap 46.2–59.4%) | 76/160 (47.5%) | 0/320 |
| Within-tolerance colluding | **38/160 (23.8%; paired-seed 95% bootstrap 18.1–30.0%)** | 122/160 (76.2%) | 0/320 |
| Beyond-tolerance colluding | 160/160 (100%) | 0/160 | 0/320 |

Within-tolerance colluding is the worst tested correct-command condition. Intervals resample whole 40-seed clusters, with 2,000 fixed paired-cluster bootstrap replicates.

### Unfamiliar and absent-command outcomes

| Membrane condition | Action on unfamiliar input | Action on absent command |
|---|---:|---:|
| Clean | **0/40** (paired bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) | **0/40** (paired bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) |
| Within-tolerance colluding | **0/40** (paired bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) | **0/40** (paired bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) |
| Beyond-tolerance colluding | **0/40** (paired bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) | **0/40** (paired bootstrap 0.0–0.0%; 40-seed Wilson 0.0–8.8%) |

Every no-command cell is 0/40, with a per-cell Wilson 95% upper bound of 8.8%; **0 observed is not zero risk.** The paired-bootstrap interval is degenerate because all sampled clusters had zero observed actions. There were no classifier exceptions, and all 1,200 trials reset as specified. This is a selected synthetic experiment, **not safety validation**.

## Run and test

From this folder:

```bash
python3 brain_propulsion.py
python3 -m unittest discover -s tests -v
(cd propulsion && python3 -m unittest tests -v)
node --test tests/brain.test.js
node evaluate_c1.js > /tmp/c1-membrane-only.json
python3 evaluate_c1_e2e_v2.py --validate-only
python3 reporting_amendment_v2.py
```

The full regression set passes **57 tests**: 32 top-level Python tests (including 10 reporting-amendment tests), 10 original propulsion tests, and 15 copied brain tests. This includes a regression for `apply_classifier(..., lambda: None)` after prior motion and tests for the cluster-aware reporting derivation. The v2 evaluator verifies the pre-data protocol/source/test hashes and refuses to overwrite existing v2 outputs. The reporting utility reads the preserved v2 JSON and writes separate amendment outputs; it does not regenerate or modify v2 data.

To call the connector from Python:

```python
from brain_propulsion import run_c1_trial

result = run_c1_trial("forward", seed="c1-demo", total_steps=2000)
print(result["membrane_gate"]["event"], result["propulsion_classifier"]["response"], result["drive"])
```

Use `probe_name="random"` to exercise classifier rejection, or `noise_sigma=0.15` with a named probe. These are generated toy vectors, not live inputs.

## Files and evidence

- `brain_propulsion.py` — resettable, fail-closed connector.
- `brain_trial.js`, `e2e_membrane_batch.js` — local model bridges; the batch bridge returns only event bits, not truth labels.
- `evaluate_c1_e2e_v2.py`, `END_TO_END_PROTOCOL_V2.md`, `END_TO_END_PROTOCOL_V2.sha256`, and `END_TO_END_FREEZE_V2.json` — frozen corrected protocol and hash record.
- `end_to_end_evaluation_v2.json` and `end_to_end_report_v2.md` — fresh full-chain v2 data and corrected report.
- `reporting_amendment_v2.py`, `end_to_end_reporting_amendment_v2.json`, and `end_to_end_report_v2_reporting_amendment.md` — additive cluster-aware reporting amendment; the original data and report remain intact.
- `tests/test_c1_none_classifier_regression.py` and `tests/test_reporting_amendment_v2.py` — additive regression and reporting tests, outside the frozen v2 test hash set.
- `REPORTING_TEST_AMENDMENT.md` — concise record of amendment scope, statistical reporting, tests, and preservation boundaries.
- `evaluation.json` and `EVALUATION.md` — preserved membrane-only results.
- `end_to_end_evaluation.json` and `end_to_end_report.md` — preserved v1 audit artifacts; per-class end-to-end rates are superseded by the pairing bug.
- `diagrams/c1-control-flow.svg`, `diagrams/c1-control-flow.png`, and `diagrams/c1-diagram-accessibility.md` — reset/no-command path and updated results.
- `propulsion/` — local extracted copy of the uploaded v0.1.0 package.

## License and source provenance

This release is designated **AGPL-3.0-only**. The root `LICENSE` is the conventional license entry point; the original `LICENSE.brain` and `propulsion/LICENSE` files are both retained as separate upstream notices and are byte-identical. Copied Membrane Arena v0.3.5 code retains its source headers, and its original citation record is preserved at [`provenance/membrane-arena/CITATION.cff`](provenance/membrane-arena/CITATION.cff). The extracted Brain Heart Propulsion v0.1.0 package retains [`propulsion/CITATION.cff`](propulsion/CITATION.cff) and its own `propulsion/LICENSE`. The release manifest records file-level provenance, license, size, and SHA-256 for every payload file.

## Limits

This is a **synthetic classical software experiment**, not a brain, nervous system, heartbeat, cardiac model, or propulsion device. There is no EEG/ECG, biosignal, human-data, medical, or hardware interface. The two simulated brain stages use separate generated inputs; the heart is a software clock, and phase-ring updates do not produce force, thrust, or physical movement. This evaluation is not safety validation and makes no safety, robustness, biological, medical, or real-world performance claim. The uploaded sensor's `omega` field is hard-coded by its source model, so C1 omits it rather than presenting it as a measurement.


## Owner-supplied reference uploads (kept separate)

These two uploads were inspected read-only. Neither was merged into C1 or used to generate the frozen v2 data, tests, or hash manifest; their files and results are not included in the C1 ZIP.

- `membrane-verification-suitev0.1.0` is a ZIP without a filename extension (SHA-256 `7358ad56c77003c5d2081a6917d9faa56066040c77e6ed8e6c81549672747cef`). Its `CITATION.cff` identifies membrane-verification-suite v0.1.0, released 2026-10-27, Jean‑François Brisson / Spark AI NLP, AGPL-3.0-only. Its archived `results.json` records 27 PASS, 0 FAIL, 1 NOT_RUN of 28 package entries from a separate workspace; it is not a run against this C1 folder. Five packages receive direct checks while most entries only rerun package-owned tests; there is no combined graph or all-package multi-seed sweep. The suite's `membrane-brain` 40/40 “CEILING” result is a separate Python API check, not C1's copied JavaScript membrane result or its end-to-end gate.
- `full-linked-system-v0.1.0.zip` (SHA-256 `aedb6ce09a7eb8e71ddf155339f424c6d7a2b895dd347d41790dee75326cd8f9`) identifies Full Linked System v0.1.0 in its `CITATION.cff` (Jean‑François Brisson / Spark AI NLP, AGPL-3.0-only). Its `DESIGN.md` says `ring.py` adapts the original brain-heart-propulsion toy's ring logic and describes a broader, separate synthetic chain. Its 7 Hz frequency curve is imposed rather than measured; movement is a phase-gradient toy law; and the sensor is a consistency check, not independent sensing. Its seed-42 `results.json` is that package's result, not C1 end-to-end performance.

Cite each artifact using its own `CITATION.cff` when discussing that artifact, with its own `README.md`, `PREREG.md`, `DESIGN.md`, and `results.json` for scope and recorded results. Keep their package-level PASS/demo outcomes separate from C1's membrane-only evaluation and corrected C1 v2 end-to-end results. Neither reference changes C1 v2 counts, protocol, or hashes.
