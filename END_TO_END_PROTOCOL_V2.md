# Frozen protocol: C1 end-to-end evaluation v2

## Question and boundary

This is a corrected follow-up to v1, which is preserved unchanged for audit but is not used for per-class interpretation: its fixed episode-index order aliased some membrane episode outputs with probe families. V2 assigns episode outputs through a frozen seed-specific shuffle before scoring. This is a generated-input software experiment only, not safety validation and not a safety, robustness, biological, medical, or hardware claim.

## Frozen design

- **Independent units:** 40 fresh seed clusters, `c1-e2e-v2-seed-001` through `c1-e2e-v2-seed-040`, disjoint from v1. Each cluster includes all conditions and probe families. Total: 40 × 3 × 10 = **1,200 trials**.
- **Membrane conditions:** clean (`mode=collude`, zero fault counts); within-tolerance colluding (`sensory=1`, `columns=1`, `mode=collude`); beyond-tolerance sensory colluding (`sensory=2`, `mode=collude`). Ten event bits per condition and seed come from the copied membrane model. The batch bridge returns only event bits, not planted/truth labels.
- **Pairing correction:** for each seed cluster, shuffle episode indices 0–9 with `random.Random("c1-e2e-v2-event-pairing::<seed>")`. Assign those indices in order to the ten probe families listed below. Reuse that same permutation for all three conditions within that seed, preserving paired condition comparisons. The shuffle is generated before classification/action and never uses class labels or event values.
- **Classifier:** use the propulsion toy with seed 42; calibrate once with its fixed procedure (100 sigma-0.15 in-pattern probes, 100 random OOD probes, calibration RNG seed 11). Freeze the resulting threshold. Use separate fresh probe seeds `c1-e2e-v2-classifier-input::<seed>::<family>`.
- **Ten families in fixed family order:** clean `forward`, `reverse`, `hold`, `rest`; sigma-0.15 noisy `forward`, `reverse`, `hold`, `rest`; unfamiliar random field; absent `no_command` with no classifier input. The shuffled membrane episode index is recorded in each raw trial. Each independent seed cluster contributes all 30 condition-family combinations.
- **Actuator rule:** one in-memory actuator object is reused, but every trial resets command, drive, ring position/phases, and clock. Only a Boolean membrane event and a known accepted named response can drive the ring. Rejected, unknown, malformed, missing, or exceptional classifier output becomes `no_command` with zero drive. Expected labels are attached only after action for scoring and never enter the gate.
- **Distinct outcomes:** report correct command on valid forward/reverse input; wrong command on any valid input; action when no command is expected (unfamiliar and absent-command cases separately); and false refusal when a valid forward/reverse input produces no motion. For hold/rest, no motion is correct.
- **Uncertainty:** all pooled rates use 2,000 bootstrap resamples of whole paired seed clusters, preserving the common seed-level episode assignment across conditions. Single-trial-per-seed cells also include 95% Wilson intervals over 40 seed clusters. Show exact numerator/denominator. If 0 events are observed, explicitly state this is not zero risk; show the finite-sample Wilson upper bound alongside any degenerate all-zero bootstrap interval.
- **Prominence rule:** the report leads with the condition having the lowest correct-command rate; ties follow the listed condition order. No threshold, mapping, or settings are changed after viewing v2 outcomes.

## Frozen outputs and stop rule

The evaluator writes only `end_to_end_evaluation_v2.json` and `end_to_end_report_v2.md`, and refuses to overwrite either. Before its first data-generation run, SHA-256 hashes are recorded for this protocol, the v2 evaluator, the membrane batch bridge, the C1 actuator connector, and all directly used model runtime sources. The v1 evaluation, report, protocol, and hash artifacts are left untouched.
