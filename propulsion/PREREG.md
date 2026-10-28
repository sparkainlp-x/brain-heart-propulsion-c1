# PREREG — brain-heart-propulsion v0.1.0

Written BEFORE the demo run. Bars are fixed here and are not
moved after seeing results.

## The link, in one paragraph

Brain decides, heart paces, propulsion moves, sensor reports.
A probe is projected on the brain membrane first. If the brain
gate refuses it, drive k = 0 and the probe does not move. If
the brain accepts it, the accepted response maps to a drive:
forward -> k = +1, reverse -> k = -1, hold -> k = 0,
rest -> k = 0 (fail-safe default: anything not explicitly
forward or reverse holds still). Propulsion moves only on
heart ticks, one tick every 10 steps. The sensor then reads
the ring from phase gradients alone, never from the intended
drive. The mapping, the tick period, and the fail-safe default
are DESIGN CHOICES, stated here, not discoveries.

## Pre-registered bars (seed 42, gate calibrated as in the
## brain/nervous packages: 100 noisy sigma 0.15 + 100 random)

- L1: clean forward probe -> accept, forward, displacement > 15 sites.
- L2: clean reverse probe -> accept, reverse, displacement < -15 sites.
- L3: clean hold probe -> accept, hold, |displacement| < 1 site.
- L4: random field -> refuse, drive 0, displacement exactly 0.
- L5: sensor after forward -> k_est = +1; after reverse -> -1;
  after hold/refuse -> 0. Omega reported is -1.000 in the
  drive frame, by construction, as in membrane-propulsion.
- L6: gate calibrates with Youden J > 0.5, tau in [0, 1].
- L7: no movement on non-tick steps: a single step() call
  that is not a heart tick moves the probe by exactly 0.
- L8: tau is unchanged after a linked run, and the number of
  stored brain patterns is still 4.

No bar is set on noisy acceptance rate beyond the tests'
existing thresholds (fresh noisy >= 35/40 in the brain
package's own test style is NOT re-imposed here; the linked
tests use >= 30/40 at sigma 0.15 to allow for the added
heart-tick and mapping steps, and report the measured rate).
