import json
import unittest

from reporting_amendment_v2 import INPUT_JSON, build_summary, clopper_pearson, render_report, sha256


class TestReportingAmendmentV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
        cls.summary = build_summary(cls.data, sha256(INPUT_JSON))

    def test_exact_zero_event_interval_for_forty_seed_clusters(self):
        low, high = clopper_pearson(0, 40)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.088, delta=0.001)

    def test_primary_no_command_summaries_separate_trials_from_clusters(self):
        rows = self.summary["primary_no_command_by_condition"]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["observed_events"], 0)
            self.assertEqual(row["observed_trials"], 80)
            self.assertEqual(row["seed_clusters_with_one_or_more_events"], 0)
            self.assertEqual(row["independent_seed_clusters"], 40)
            self.assertEqual(row["cluster_event_fraction_exact_binomial_95"][0], 0.0)
            self.assertAlmostEqual(row["cluster_event_fraction_exact_binomial_95"][1], 0.088, delta=0.001)

    def test_no_command_family_cells_preserve_each_forty_trial_denominator(self):
        rows = self.summary["no_command_by_condition_and_probe_family"]
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["observed_events"], 0)
            self.assertEqual(row["observed_trials"], 40)
            self.assertEqual(row["seed_clusters_with_one_or_more_events"], 0)
            self.assertEqual(row["independent_seed_clusters"], 40)

    def test_valid_wrong_command_is_a_distinct_pooled_zero_event_endpoint(self):
        rows = self.summary["primary_valid_wrong_command_by_condition"]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["observed_events"], 0)
            self.assertEqual(row["observed_trials"], 320)
            self.assertEqual(row["seed_clusters_with_one_or_more_events"], 0)
            self.assertEqual(row["independent_seed_clusters"], 40)
            self.assertAlmostEqual(row["cluster_event_fraction_exact_binomial_95"][1], 0.088, delta=0.001)

    def test_beyond_tolerance_false_refusal_reports_trials_and_cluster_incidence(self):
        summary = self.summary["primary_beyond_tolerance_false_refusal"]
        self.assertEqual(summary["condition"], "beyond_tolerance_colluding")
        self.assertEqual(summary["observed_events"], 0)
        self.assertEqual(summary["observed_trials"], 160)
        self.assertEqual(summary["opportunities_per_seed_cluster"], 4)
        self.assertEqual(summary["seed_clusters_with_one_or_more_events"], 0)
        self.assertEqual(summary["independent_seed_clusters"], 40)
        self.assertEqual(summary["event_seed_clusters"], [])
        low, high = summary["cluster_event_fraction_exact_binomial_95"]
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.088, delta=0.001)

        rows = [
            row for row in self.data["trials"]
            if row["condition"] == "beyond_tolerance_colluding"
            and row["probe_kind"] == "valid"
            and row["target_class_for_scoring_only"] in ("forward", "reverse")
        ]
        per_seed = {seed: 0 for seed in self.data["metadata"]["seed_clusters"]}
        for row in rows:
            per_seed[row["seed_cluster"]] += 1
        self.assertEqual(len(rows), 160)
        self.assertEqual(set(per_seed.values()), {4})

    def test_cross_condition_pool_is_marked_sensitivity_not_primary(self):
        no_command = self.summary["sensitivity_all_conditions_no_command"]
        wrong = self.summary["sensitivity_all_conditions_valid_wrong_command"]
        self.assertEqual((no_command["observed_events"], no_command["observed_trials"]), (0, 240))
        self.assertEqual((wrong["observed_events"], wrong["observed_trials"]), (0, 960))
        self.assertIn("Sensitivity", no_command["scope"])
        self.assertIn("Sensitivity", wrong["scope"])

    def test_worst_correct_command_result_is_first_reported_result(self):
        report = render_report(self.summary)
        result_marker = "**Worst tested correct-command result:**"
        zero_event_header = "## Primary zero-event estimates by condition"
        self.assertLess(report.index(result_marker), report.index(zero_event_header))
        self.assertIn("Within-tolerance colluding", report)
        self.assertIn("38/160 (23.8%)", report)

    def test_report_separates_trial_denominators_from_cluster_uncertainty(self):
        report = render_report(self.summary)
        self.assertIn("0/80", report)
        self.assertIn("0/320", report)
        self.assertIn("0/240", report)
        self.assertIn("not a per-trial risk interval", report)
        self.assertIn("Zero observed events do not establish zero risk", report)
        self.assertIn("paired-cluster bootstrap is degenerate", report)
        self.assertIn("False refusal on valid directional probes", report)
        self.assertIn("0/160", report)
        self.assertIn("0.0%–8.8%", report)
        self.assertIn("fraction of clusters with at least one false refusal", report)

    def test_invalid_exact_interval_inputs_are_rejected(self):
        for args in ((0, 0), (-1, 40), (41, 40), (True, 40)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                clopper_pearson(*args)


if __name__ == "__main__":
    unittest.main()
