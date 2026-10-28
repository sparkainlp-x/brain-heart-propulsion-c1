# C1 evaluation: two separate synthetic brain stages

C1 combines two toy stages with an AND gate: the copied membrane model must emit a consensus event, and the propulsion package's separate calibrated classifier must accept a generated named probe. The classifier's named response provides the toy direction. The models use **separate inputs**; no membrane vector is fed into the other classifier. Neither stage is a biological brain.

## Membrane-event batch results

The reproducible batch used **five fixed seeds × 100 episodes** per condition: 500 synthetic episodes, split evenly between planted-pattern and noise episodes. These figures measure the membrane event stage only; they do not include the separate classifier's acceptance rate or claim full-chain movement performance.

| Condition | True outputs on planted episodes | False activations on noise episodes | Membrane event activations |
|---|---:|---:|---:|
| Clean | 246/250 (98.4%; 95% Wilson interval 96.0–99.4%) | 0/250 (0%; interval 0–1.51%) | 246/500 |
| Within tolerance: one colluding sensory member per column plus one colluding gate | 127/250 (50.8%; interval 44.6–56.9%) | 0/250 (0%; interval 0–1.51%) | 127/500 |
| Beyond tolerance: two colluding sensory members per column | 0/250 (0%; interval 0–1.51%) | 250/250 (100%; interval 98.5–100%) | 500/500 |

The within-tolerance condition kept false activations at zero in this sample but reduced recall to 50.8%. The beyond-tolerance condition defeated the membrane event gate in this setup. Zero observed is not proof of zero risk: the 95% Wilson upper bound is about 1.51% for 0/250.

## The other classifier and end-to-end checks

The uploaded propulsion toy's own regression suite passed **10/10** tests, covering its calibration, forward/reverse/hold behavior, random-field refusal, heart ticks, and noisy-forward recognition. Its included seed-42 demo reports gate threshold **0.257**, Youden J **0.990**, and **40/40** fresh noisy-forward probes recognized at sigma 0.15. These characterize that separate toy classifier; they are not an end-to-end C1 accuracy estimate.

C1's new tests verify forward and reverse recognition, stationary hold/rest, classifier refusal, and that an otherwise-valid classifier response still produces no movement when the membrane event is absent. A basic forward demo produces about **19.63 modeled ring sites over 200 software-clock ticks**. None of this is physical movement or real-world control.

## Limits

The Wilson intervals are descriptive model-frequency intervals. All inputs are generated software vectors; the fault scenarios are selected experiments, not estimates of real fault rates. C1 has no EEG/ECG, human data, sensor hardware, heartbeat, force, or propulsion device. Its heart is a 10-step clock and its ring is an in-memory phase-gradient model. The uploaded `omega` sensor field is omitted because its source hard-codes that value.

Regenerate the machine-readable membrane-stage counts with `node evaluate_c1.js`; see [`evaluation.json`](evaluation.json). The full local code and commands are in [`README.md`](README.md).
