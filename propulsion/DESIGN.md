# DESIGN.md — brain-heart-propulsion v0.1.0

## Why this link, and what it reuses

membrane-brain already decides, membrane-heart already paces
with a pacemaker seed, and membrane-propulsion already moves
a probe and reads it back with a passive sensor. The linked
toy does not merge those packages into one graph: it keeps
three stages with three jobs, and wires decision -> tick ->
movement -> sensor readout. That separation is what makes a
refusal testable: a refused probe must produce zero movement,
not a slower movement.

## Decisions

- Brain patterns are waves seeded at nodes 0, 32, 64, 96,
  named forward, reverse, hold, rest. The names are labels
  on the mapping, not properties of the waves.
- Mapping is fail-safe by default: only forward and reverse
  move. Hold and rest both give k = 0. An unmapped accepted
  pattern would also hold, by the same rule, rather than
  invent a direction.
- Heart is a clock with period 10 steps. Using the heart
  graph's full wave field as a clock would have added a
  second 64-node graph and a second Dijkstra pass for no
  measured gain in this link; the clock is stated as a clock.
- Propulsion ring phases are set to the locked twist for
  the chosen drive, as in the locked seed-42 propulsion
  case. The toy does not simulate Kuramoto locking from a
  random start; that locking is already measured in
  membrane-propulsion.
- Sensor coherence here is gradient spread, so a perfect
  twist scores 1.000. It is not membrane-propulsion's
  sensor coherence (0.990), and the README says so.

## Falsified / not built

- A brain wave that directly drives the ring phase without
  a gate: not built. The gate must pass first, or k = 0.
- Movement on every step: not built. Non-tick steps move
  exactly 0, test-pinned.
- A heart rate, ECG, or cardiac output: not built, not claimed.
- Learning across runs: not built. Each run recalibrates
  nothing and stores nothing new.
