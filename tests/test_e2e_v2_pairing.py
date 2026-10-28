import unittest

from evaluate_c1_e2e_v2 import PROBE_FAMILIES, event_order_for_seed


class TestV2EventPairing(unittest.TestCase):
    def test_each_seed_gets_a_stable_full_permutation_not_fixed_family_order(self):
        expected = list(range(len(PROBE_FAMILIES)))
        first_seed = "c1-e2e-v2-seed-001"
        order = event_order_for_seed(first_seed)
        self.assertEqual(sorted(order), expected)
        self.assertEqual(order, event_order_for_seed(first_seed))
        self.assertNotEqual(order, expected)

    def test_distinct_seed_clusters_get_independent_pairing_orders(self):
        self.assertNotEqual(
            event_order_for_seed("c1-e2e-v2-seed-001"),
            event_order_for_seed("c1-e2e-v2-seed-002"),
        )

    def test_v2_family_matrix_still_covers_all_requested_inputs(self):
        self.assertEqual(len(PROBE_FAMILIES), 10)
        self.assertEqual(
            {family["target_class"] for family in PROBE_FAMILIES if family["kind"] == "valid"},
            {"forward", "reverse", "hold", "rest"},
        )
        self.assertEqual(sum(family["quality"] == "clean" for family in PROBE_FAMILIES), 4)
        self.assertEqual(sum(family["quality"] == "noisy_sigma_0.15" for family in PROBE_FAMILIES), 4)
        self.assertEqual({family["id"] for family in PROBE_FAMILIES if family["kind"] != "valid"}, {"unfamiliar_random", "no_command"})


if __name__ == "__main__":
    unittest.main()
