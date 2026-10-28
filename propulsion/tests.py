"""Tests for brain-heart-propulsion v0.1.0.
Run: python3 -m unittest tests -v
Bars are from PREREG.md.
"""
import math
import random
import unittest

from linked import (BRAIN_N, Brain, HeartClock, LinkedSystem,
                    PropulsionRing, noisy, rand_field)


def calibrated():
    sys = LinkedSystem(seed=42)
    sys.calibrate()
    return sys


class TestLinked(unittest.TestCase):
    def test_stage_counts(self):
        sys = LinkedSystem(seed=42)
        self.assertEqual(len(sys.brain.graph.pts), 128)
        self.assertEqual(len(sys.brain.patterns), 4)
        self.assertEqual(sys.ring.n, 64)

    def test_gate_calibrates_prereg_l6(self):
        sys = LinkedSystem(seed=42)
        tau, j = sys.calibrate()
        self.assertGreater(j, 0.5)
        self.assertTrue(0.0 <= tau <= 1.0)

    def test_forward_prereg_l1_l5(self):
        sys = calibrated()
        res = sys.run(sys.brain.patterns[0])
        self.assertEqual((res.decision, res.response), ("accept", "forward"))
        self.assertEqual(res.drive, 1)
        self.assertGreater(res.displacement, 15)
        self.assertEqual(res.sensor["k_est"], 1)

    def test_reverse_prereg_l2_l5(self):
        sys = calibrated()
        res = sys.run(sys.brain.patterns[1])
        self.assertEqual((res.decision, res.response), ("accept", "reverse"))
        self.assertEqual(res.drive, -1)
        self.assertLess(res.displacement, -15)
        self.assertEqual(res.sensor["k_est"], -1)

    def test_hold_prereg_l3_l5(self):
        sys = calibrated()
        res = sys.run(sys.brain.patterns[2])
        self.assertEqual((res.decision, res.response), ("accept", "hold"))
        self.assertEqual(res.drive, 0)
        self.assertAlmostEqual(res.displacement, 0.0, places=6)
        self.assertEqual(res.sensor["k_est"], 0)

    def test_random_refused_prereg_l4(self):
        sys = calibrated()
        rng = random.Random(7)
        res = sys.run(rand_field(BRAIN_N, rng))
        self.assertEqual(res.decision, "reject")
        self.assertEqual(res.drive, 0)
        self.assertEqual(res.displacement, 0.0)

    def test_no_move_on_non_tick_prereg_l7(self):
        clock = HeartClock()
        ring = PropulsionRing()
        ring.set_drive(1)
        start = ring.position
        # Step 1 is not a tick (period 10): no movement by design.
        self.assertFalse(clock.step())
        self.assertEqual(ring.position, start)

    def test_heart_ticks_count(self):
        sys = calibrated()
        res = sys.run(sys.brain.patterns[0], total_steps=2000)
        self.assertEqual(res.heart_ticks, 200)

    def test_tau_unchanged_prereg_l8(self):
        sys = calibrated()
        tau_before = sys.brain.tau
        sys.run(sys.brain.patterns[0])
        self.assertEqual(sys.brain.tau, tau_before)
        self.assertEqual(len(sys.brain.patterns), 4)

    def test_fresh_noisy_forward(self):
        sys = calibrated()
        rng = random.Random(99)
        ok = 0
        for k in range(40):
            probe = noisy(sys.brain.patterns[0], 0.15, rng)
            res = sys.run(probe)
            if res.decision == "accept" and res.response == "forward":
                ok += 1
        self.assertGreaterEqual(ok, 30)


if __name__ == "__main__":
    unittest.main()
