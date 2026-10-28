import unittest

from evaluate_c1_e2e_v2 import (
    PROBE_FAMILIES,
    cluster_interval,
    score_after_actuation,
    wilson,
)


class TestEndToEndEvaluation(unittest.TestCase):
    def _raw(self, action, prediction="forward"):
        return {
            "seed_cluster": "test-seed",
            "condition": "clean",
            "actual_action": action,
            "classifier_prediction": prediction,
            "classifier_decision": "accept" if prediction not in ("reject", "no_command") else prediction,
        }

    def _family(self, target, kind="valid"):
        return {
            "id": f"probe-{target or kind}",
            "kind": kind,
            "quality": "test",
            "target_class": target,
            "sigma": None,
        }

    def test_protocol_matrix_crosses_all_classes_qualities_conditions_and_controls(self):
        self.assertEqual(len(PROBE_FAMILIES), 10)
        self.assertEqual(
            {f["target_class"] for f in PROBE_FAMILIES if f["kind"] == "valid"},
            {"forward", "reverse", "hold", "rest"},
        )
        self.assertEqual(sum(f["quality"] == "clean" for f in PROBE_FAMILIES), 4)
        self.assertEqual(sum(f["quality"] == "noisy_sigma_0.15" for f in PROBE_FAMILIES), 4)
        self.assertIn("unfamiliar_random", {f["id"] for f in PROBE_FAMILIES})
        self.assertIn("no_command", {f["id"] for f in PROBE_FAMILIES})

    def test_directional_correct_command_wrong_command_and_false_refusal_are_distinct(self):
        correct = score_after_actuation(self._raw("forward"), self._family("forward"))
        refusal = score_after_actuation(self._raw("none"), self._family("forward"))
        wrong = score_after_actuation(self._raw("reverse", "reverse"), self._family("forward"))
        self.assertEqual(correct["scored_outcome"], "correct_command")
        self.assertTrue(correct["correct_command"])
        self.assertEqual(refusal["scored_outcome"], "false_refusal")
        self.assertTrue(refusal["false_refusal"])
        self.assertEqual(wrong["scored_outcome"], "wrong_command")
        self.assertTrue(wrong["wrong_command"])

    def test_hold_and_rest_no_motion_are_correct_but_movement_is_wrong_command(self):
        for target in ("hold", "rest"):
            with self.subTest(target=target):
                still = score_after_actuation(self._raw("none", target), self._family(target))
                moving = score_after_actuation(self._raw("forward", target), self._family(target))
                self.assertEqual(still["scored_outcome"], "correct_no_action")
                self.assertFalse(still["false_refusal"])
                self.assertEqual(moving["scored_outcome"], "wrong_command")

    def test_action_when_no_command_expected_is_separate_for_noise_and_absence(self):
        for kind in ("unfamiliar", "no_command"):
            with self.subTest(kind=kind):
                family = self._family(None, kind)
                no_action = score_after_actuation(self._raw("none", "no_command"), family)
                false_action = score_after_actuation(self._raw("reverse", "no_command"), family)
                self.assertEqual(no_action["scored_outcome"], "no_action")
                self.assertFalse(no_action["action_on_expected_no_command"])
                self.assertEqual(false_action["scored_outcome"], "action_on_expected_no_command")
                self.assertTrue(false_action["action_on_expected_no_command"])

    def test_seed_level_uncertainty_does_not_turn_zero_observed_into_zero_risk(self):
        lo, hi = wilson(0, 40)
        self.assertEqual(lo, 0)
        self.assertGreater(hi, 0.08)
        seeds = ["s1", "s2", "s3", "s4"]
        rows = [{"seed_cluster": seed, "hit": seed == "s1"} for seed in seeds]
        draws = [[0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 2, 3], [3, 3, 3, 3]]
        result = cluster_interval(rows, seeds, draws, lambda r: r["hit"], lambda _r: True)
        self.assertEqual(result["successes"], 1)
        self.assertEqual(result["observations"], 4)
        self.assertEqual(result["seed_clusters"], 4)
        self.assertNotEqual(result["seed_cluster_bootstrap_95"][0], result["seed_cluster_bootstrap_95"][1])


if __name__ == "__main__":
    unittest.main()
