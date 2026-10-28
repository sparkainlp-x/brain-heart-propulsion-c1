# C1 control-flow diagram (corrected v2)

## Short caption
C1 is a software-only toy connection between separate synthetic membrane and command inputs. Each trial resets drive, ring state, and clock. Accepted, known commands may update an in-memory phase ring; rejected, unknown, malformed, missing, or exceptional classifier output follows a visible **NO-COMMAND → DRIVE 0** path. This is **not safety validation** and is **NOT A SAFETY GUARANTEE**.

## Long description
Read the actual software path from left to right. A banner states that the system uses synthetic inputs and software only, has no neural or ECG data, and produces no physical movement. For v2, a seed-specific shuffle assigns ten membrane episode outputs to ten classifier probe families; the same shuffle is reused across all three conditions within each of 40 seed clusters.

The two input branches are separate. Synthetic Input A supplies generated membrane vectors to the membrane permission model, which emits or withholds an event. Synthetic Input B supplies an independently generated probe to the command classifier. Every trial clears drive and resets ring position/phases and clock before classification. A known accepted response reaches the AND stage only with a Boolean membrane event. Rejected, unknown, malformed, missing, or exceptional classifier output becomes `no_command`; a missing permission event also blocks the command. The visible no-command branch bypasses named-response mapping and sends drive zero to the software scheduler. The gate prominently says **NOT A SAFETY GUARANTEE**.

If the gate passes, mapping is `forward` → +1, `reverse` → −1, and `hold` or `rest` → 0. A 10-simulation-step software clock updates an in-memory 64-site phase ring. Its passive readout reports values derived from the ring phases; it is not independent sensing. An orange dashed loop is a self-check of that same toy state.

## Results shown
**V1 per-class end-to-end rates are superseded by a pairing bug.** V1's fixed episode-index assignment aliased some episodes to probe families. It is retained for audit only and its per-class rates are not interpreted. The corrected v2 results use a seed-specific shuffled pairing, shared across conditions.

The red collusion panel first shows membrane-permission-stage-only results from 500 episodes per condition: clean, 246/250 planted detections and 0/250 noise activations; within-tolerance collusion, 127/250 and 0/250; beyond tolerance, 0/250 planted detections and 250/250 noise activations. These counts are not end-to-end action rates.

**Valid commands:** Correct forward/reverse commands were 84/160 clean, 38/160 within tolerance, and 160/160 beyond tolerance. The worst tested condition is within-tolerance colluding: 38/160 (23.8%; 95% paired-seed-cluster interval 18.1–30.0%). False refusals were 76/160, 122/160, and 0/160, respectively; wrong commands were 0/320 in each condition.

**Unfamiliar and absent-command inputs:** In all six cells (two probe types × three conditions), actions were **0/40**. Each cell's 95% Wilson upper bound is **8.8%**; each paired-cluster bootstrap interval is 0–0% because every sampled seed was zero. **0 observed is not zero risk.** The per-class confusion table uses 40-seed denominators; each `0/40` cell has the same 95% Wilson upper bound of 8.8%.

These selected generated-input results are not safety validation. All 1,200 v2 trials reset. The batch helper returns membrane event bits only, never ground-truth labels, and the expected labels are used only after simulated action for scoring.

## Explanatory metaphor layer
A muted dashed band labels “brain,” “heart,” and “propulsion” as analogies only, not implemented or measured. No biological brain, heartbeat, ECG, actuator, force, thrust, or physical movement is present. The implementation makes no safety, robustness, biological, medical, or hardware claim.

## Visual key
- **Solid blue arrows:** software data and control flow, including the zero-drive branch.
- **Orange dashed arrow:** read-only internal self-check loop.
- **Muted gray dashed panel and borders:** explanatory metaphors only.
- **Red panel:** membrane-stage stress results are distinguished from v2 end-to-end action outcomes.
