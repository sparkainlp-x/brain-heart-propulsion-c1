import unittest

from brain_propulsion import C1Actuator


class TestClassifierNoneAfterPriorMotion(unittest.TestCase):
    def test_none_output_after_forward_motion_resets_to_no_command(self):
        actuator = C1Actuator()
        prior = actuator.apply_classifier(
            True,
            lambda: ("accept", "forward", "forward"),
            total_steps=2_000,
        )
        self.assertEqual(prior["drive"], 1)
        self.assertGreater(prior["propulsion"]["displacement"], 0.0)

        next_trial = actuator.apply_classifier(True, lambda: None, total_steps=2_000)

        self.assertEqual(next_trial["classifier_error_type"], "malformed_output")
        self.assertEqual(next_trial["classifier_decision"], "no_command")
        self.assertIsNone(next_trial["classifier_response"])
        self.assertFalse(next_trial["combined_gate_passed"])
        self.assertEqual(next_trial["drive"], 0)
        self.assertEqual(next_trial["propulsion"]["start_position"], 0.0)
        self.assertEqual(next_trial["propulsion"]["final_position"], 0.0)
        self.assertEqual(next_trial["propulsion"]["displacement"], 0.0)
        self.assertEqual(next_trial["heart"]["ticks"], 200)
        self.assertEqual(actuator.last_drive, 0)
        self.assertEqual(actuator.ring.drive, 0)
        self.assertEqual(actuator.ring.position, 0.0)


if __name__ == "__main__":
    unittest.main()
