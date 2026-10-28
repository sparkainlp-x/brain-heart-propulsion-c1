# Frozen protocol: C1 end-to-end evaluation v1

## Question and boundary

Measure C1's simulated end-to-end outputs when the membrane permission model and the propulsion package's classifier receive **separate generated inputs**. This is a software-model comparison only; it makes no safety, robustness, biological, medical, or hardware claim. The existing membrane-only `evaluation.json` remains a separate artifact and is not overwritten.

## Frozen design

- **Independent units:** 40 seed clusters, `c1-e2e-seed-001` through `c1-e2e-seed-040`. Each cluster contains all conditions and probe families; fault-condition comparisons are paired within seed. Total: 40 × 3 × 10 = **1,200 end-to-end trials**.
- **Membrane conditions:** clean (`mode=collude`, zero fault counts); within-tolerance colluding (`sensory=1`, `columns=1`, `mode=collude`); beyond-tolerance sensory colluding (`sensory=2`, `mode=collude`). The same membrane seed is reused across the three conditions within a cluster. Ten output-event bits come from ten episodes of the copied membrane model. Only the event bit enters the C1 gate; no planted/truth label is returned by the batch bridge.
- **Classifier:** instantiate the uploaded toy classifier with seed 42 and calibrate once using its built-in fixed procedure (100 sigma-0.15 in-pattern probes, 100 random out-of-distribution probes, calibration RNG seed 11). Freeze that threshold for all evaluation probes.
- **Ten probe families per cluster and condition:** in fixed order, clean `forward`, `reverse`, `hold`, `rest`; noisy sigma-0.15 `forward`, `reverse`, `hold`, `rest`; unfamiliar random field; no-command with no classifier input. Membrane episode indices 0–9 pair with this order. The classifier probe randomness uses a separate seed namespace from the membrane simulation. The four clean probes are the classifier's stored templates.
- **Action/reset rule:** the evaluator reuses one actuator object, but every trial resets command, drive, ring position/phases, and clock before classification. Only a known accepted response with a Boolean membrane event can drive the simulated ring. Unknown, rejected, malformed, missing, or exceptional classifier output becomes `no_command` with zero drive. Expected class labels are attached only after the action result for scoring; they never enter the gate or actuator.
- **Scoring:** confusion rows compare valid probes with `forward/reverse/hold/rest/reject`. Report four distinct outcome types: correct command on valid forward/reverse input; wrong command on any valid input (wrong direction or unexpected hold/rest motion); action when no command is expected (unfamiliar field or absent command, shown separately); and false refusal when a valid forward/reverse input produces no movement. For hold/rest, no movement is correct.
- **Uncertainty:** every pooled interval uses 2,000 bootstrap resamples of whole paired seed clusters, preserving the 40-cluster design rather than treating 1,200 trials as independent. Single-trial-per-seed cells also report 95% Wilson intervals over the 40 independent seeds. Bootstrap RNG seed: 20261027. Include raw trial records and per-seed cluster counts.

## Fixed outputs and stopping rule

The evaluator uses exactly these three fault conditions, ten probe families, 40 seed clusters, 10 membrane episodes per run, 2,000 heart-clock steps per trial, and 2,000 cluster-bootstrap replicates. It writes a new `end_to_end_evaluation.json` and `end_to_end_report.md` only if those paths do not already exist. Before the first evaluation run, SHA-256 hashes are recorded for this protocol, the evaluator, the membrane batch bridge, the C1 actuator connector, and all directly used model runtime sources. No settings or thresholds are changed after observing results.
