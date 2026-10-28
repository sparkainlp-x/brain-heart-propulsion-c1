import unittest

from brain_propulsion import C1Actuator, apply_composite_gate, run_brain_event, run_c1_trial
from propulsion.linked import HeartClock, PropulsionRing


class TestC1Connector(unittest.TestCase):
    def test_forward_requires_both_stages_and_moves_on_clock_ticks(self):
        result = run_c1_trial("forward", seed="c1-demo", total_steps=2_000)
        self.assertTrue(result["synthetic"])
        self.assertTrue(result["membrane_gate"]["event"])
        self.assertEqual(result["propulsion_classifier"]["decision"], "accept")
        self.assertEqual(result["propulsion_classifier"]["response"], "forward")
        self.assertTrue(result["combined_gate_passed"])
        self.assertEqual(result["proposed_drive"], 1)
        self.assertEqual(result["drive"], 1)
        self.assertEqual(result["heart"]["ticks"], 200)
        self.assertGreater(result["propulsion"]["displacement"], 15)
        self.assertEqual(result["sensor"]["k_est"], 1)
        self.assertNotIn("omega", result["sensor"])

    def test_reverse_direction_comes_from_the_separate_classifier(self):
        result = run_c1_trial("reverse", seed="c1-demo", total_steps=2_000)
        self.assertTrue(result["membrane_gate"]["event"])
        self.assertEqual(result["propulsion_classifier"]["response"], "reverse")
        self.assertEqual(result["proposed_drive"], -1)
        self.assertEqual(result["drive"], -1)
        self.assertLess(result["propulsion"]["displacement"], -15)
        self.assertEqual(result["sensor"]["k_est"], -1)

    def test_no_membrane_event_blocks_a_valid_classifier_response(self):
        result = run_c1_trial(
            "forward",
            seed="c1-abstain",
            total_steps=2_000,
            faults={"sensory": 3, "sensoryColumns": 3, "mode": "silent"},
        )
        self.assertFalse(result["membrane_gate"]["event"])
        self.assertEqual(result["propulsion_classifier"]["response"], "forward")
        self.assertEqual(result["proposed_drive"], 1)
        self.assertFalse(result["combined_gate_passed"])
        self.assertEqual(result["drive"], 0)
        self.assertEqual(result["propulsion"]["displacement"], 0.0)
        self.assertEqual(result["sensor"]["k_est"], 0)

    def test_classifier_rejection_blocks_even_when_membrane_gate_emits(self):
        result = run_c1_trial("random", seed="c1-demo", total_steps=2_000)
        self.assertTrue(result["membrane_gate"]["event"])
        self.assertEqual(result["propulsion_classifier"]["decision"], "no_command")
        self.assertFalse(result["combined_gate_passed"])
        self.assertEqual(result["drive"], 0)
        self.assertEqual(result["propulsion"]["displacement"], 0.0)

    def test_no_command_cannot_create_action_from_a_membrane_event(self):
        result = run_c1_trial("no_command", seed="c1-demo", total_steps=2_000)
        self.assertTrue(result["membrane_gate"]["event"])
        self.assertEqual(result["propulsion_classifier"]["decision"], "no_command")
        self.assertIsNone(result["propulsion_classifier"]["response"])
        self.assertFalse(result["combined_gate_passed"])
        self.assertEqual(result["proposed_drive"], 0)
        self.assertEqual(result["drive"], 0)
        self.assertEqual(result["propulsion"]["displacement"], 0.0)

    def test_hold_and_rest_are_recognized_but_stationary(self):
        for probe_name in ("hold", "rest"):
            with self.subTest(probe_name=probe_name):
                result = run_c1_trial(probe_name, seed="c1-demo", total_steps=2_000)
                self.assertTrue(result["membrane_gate"]["event"])
                self.assertEqual(result["propulsion_classifier"]["decision"], "accept")
                self.assertEqual(result["propulsion_classifier"]["response"], probe_name)
                self.assertTrue(result["combined_gate_passed"])
                self.assertEqual(result["drive"], 0)
                self.assertEqual(result["propulsion"]["displacement"], 0.0)

    def test_noisy_named_probe_uses_calibrated_classifier(self):
        result = run_c1_trial("forward", seed="c1-demo", noise_sigma=0.15)
        self.assertGreater(result["propulsion_classifier"]["youden_j"], 0.5)
        self.assertTrue(0 <= result["propulsion_classifier"]["tau"] <= 1)
        self.assertEqual(result["propulsion_classifier"]["response"], "forward")

    def test_exception_after_prior_forward_resets_to_no_command(self):
        actuator = C1Actuator()
        prior = actuator.apply(True, "accept", "forward", total_steps=2_000)
        self.assertEqual(prior["drive"], 1)

        def raises():
            raise RuntimeError("synthetic classifier failure")

        next_trial = actuator.apply_classifier(True, raises, total_steps=2_000)
        self.assertEqual(next_trial["classifier_error_type"], "RuntimeError")
        self.assertEqual(next_trial["classifier_decision"], "no_command")
        self.assertEqual(next_trial["drive"], 0)
        self.assertEqual(next_trial["propulsion"]["start_position"], 0.0)
        self.assertEqual(next_trial["propulsion"]["final_position"], 0.0)
        self.assertEqual(next_trial["propulsion"]["displacement"], 0.0)
        self.assertEqual(next_trial["heart"]["ticks"], 200)

    def test_malformed_or_missing_output_after_prior_reverse_cannot_stick(self):
        actuator = C1Actuator()
        prior = actuator.apply(True, "accept", "reverse", total_steps=2_000)
        self.assertEqual(prior["drive"], -1)
        malformed = actuator.apply_classifier(True, lambda: {"decision": "accept"}, total_steps=2_000)
        self.assertEqual(malformed["classifier_decision"], "no_command")
        self.assertEqual(malformed["classifier_error_type"], "malformed_output")
        self.assertEqual(malformed["drive"], 0)
        self.assertEqual(malformed["propulsion"]["displacement"], 0.0)
        missing = actuator.apply(True, None, None, total_steps=2_000)
        self.assertEqual(missing["classifier_decision"], "no_command")
        self.assertEqual(missing["drive"], 0)
        self.assertEqual(missing["propulsion"]["final_position"], 0.0)

    def test_unknown_rejected_or_invalid_responses_default_to_no_command(self):
        for decision, response in (("reject", "forward"), ("maybe", "reverse"), ("accept", "sideways"), ("accept", None)):
            with self.subTest(decision=decision, response=response):
                result = apply_composite_gate(True, decision, response, total_steps=100)
                self.assertEqual(result["classifier_decision"], "no_command")
                self.assertEqual(result["classifier_response"], None)
                self.assertEqual(result["drive"], 0)
                self.assertEqual(result["propulsion"]["displacement"], 0.0)

    def test_explicit_reset_clears_drive_ring_position_and_clock(self):
        actuator = C1Actuator()
        actuator.apply(True, "accept", "forward", total_steps=2_000)
        actuator.reset()
        self.assertEqual(actuator.last_drive, 0)
        self.assertEqual(actuator.ring.drive, 0)
        self.assertEqual(actuator.ring.position, 0.0)
        self.assertEqual(actuator.clock.ticks, 0)

    def test_membrane_event_api_does_not_expose_hidden_truth_label(self):
        event = run_brain_event("c1-demo")
        self.assertIsInstance(event["event"], bool)
        self.assertNotIn("outTrue", event)

    def test_no_motion_before_a_heart_clock_tick(self):
        clock = HeartClock(period_steps=10)
        ring = PropulsionRing(n=64)
        ring.set_drive(1)
        start = ring.position
        self.assertFalse(clock.step())
        self.assertEqual(ring.position, start)

    def test_inputs_are_bounded_and_explicit(self):
        with self.assertRaises(ValueError):
            run_c1_trial("left")
        with self.assertRaises(ValueError):
            run_c1_trial("forward", total_steps=-1)
        with self.assertRaises(ValueError):
            run_c1_trial("forward", total_steps=True)
        with self.assertRaises(ValueError):
            run_c1_trial("forward", noise_sigma=-0.1)
        with self.assertRaises(ValueError):
            run_brain_event("x" * 41)


if __name__ == "__main__":
    unittest.main()
