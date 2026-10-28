# brain-heart-propulsion v0.1.0

**Brain decides, heart paces, propulsion moves, sensor reports —
a synthetic linked toy, not a brain, a heart, or a propulsion device.**

Stdlib-only Python, seeded, reproducible, AGPL-3.0-only.

## Run

```bash
python demo.py    # linked demo, seed 42
python3 -m unittest tests -v  # 10 tests
```

## The link, in one paragraph

A probe is projected on a 128-node brain membrane first. If the
brain gate refuses it, drive k = 0 and nothing moves. If the
brain accepts it, the response maps to a drive: forward -> +1,
reverse -> -1, hold -> 0, rest -> 0 (fail-safe default).
Propulsion moves only on heart ticks, one tick every 10 steps.
The ring sensor then reads k_est, omega, and coherence from
phase gradients alone, never from the intended drive.

## Measured (demo, seed 42)

- Brain gate: tau = **0.257**, Youden J = **0.990** (frozen)
- Forward: accept, forward, drive +1, displacement **+19.63** sites,
  200 heart ticks, sensor k_est **+1**, omega -1.000, coherence 1.000
- Reverse: accept, reverse, drive -1, displacement **-19.63** sites,
  sensor k_est **-1**
- Hold: accept, hold, drive 0, displacement **0.00**, sensor k_est 0
- Rest: accept, rest, drive 0, displacement **0.00**, sensor k_est 0
- Random field: **refuse**, drive 0, displacement 0.00, sensor k_est 0
- Fresh noisy forward (sigma 0.15): **40/40** correct
- Tau after runs: 0.257 (unchanged), patterns still 4

Displacement is 19.63, not 20, because the twist gradient is
2*pi/64 = 0.09817 per tick x 200 ticks. That is by construction,
as in membrane-propulsion, and is reported exactly, not rounded
to the older +20. Sensor coherence is 1.000 here because this
sensor defines coherence as gradient spread on a perfect twist;
membrane-propulsion's sensor reported 0.990 under its own
definition. The two coherence numbers are not the same measure.

## Honest limits — read before any use

- **Not a brain, not a heart, not a nervous system, not a
  propulsion device, not neuroscience, not a medical device,
  not a diagnosis, not a measurement of any real person.**
- The heart is a clock (one tick every 10 steps), not a
  heartbeat, ECG, or cardiac model. Its period is chosen.
- The brain-heart-propulsion mapping is imposed in PREREG.md,
  not discovered. A different mapping would give different
  movement, and that would still be a toy choice.
- Probe movement is an assumed law (velocity = phase
  gradient), not thrust, force, or a physical drive.
- Delays are distance units, not milliseconds. Frequencies
  are arbitrary toy units unless a module says otherwise.
- No human data were used, and no human experiments were
  conducted. This package contains only generated toy vectors.

## Files

- `linked.py` — brain graph, heart clock, propulsion ring, sensor, link
- `demo.py` — measured demo
- `tests.py` — 10 tests
- `PREREG.md` — pre-registered bars, written before the demo run
- `DESIGN.md` — decisions, falsified designs, limits
- `LICENSE` — AGPL-3.0-only
