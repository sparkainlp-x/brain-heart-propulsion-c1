#!/usr/bin/env python3
"""Create additive cluster-aware summaries from the immutable v2 result JSON.

This is a reporting amendment only: it never reruns or edits the frozen evaluator,
protocol, freeze record, or v2 trial data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
INPUT_JSON = ROOT / "end_to_end_evaluation_v2.json"
OUTPUT_JSON = ROOT / "end_to_end_reporting_amendment_v2.json"
OUTPUT_MD = ROOT / "end_to_end_report_v2_reporting_amendment.md"
NO_COMMAND_KINDS = {"unfamiliar", "no_command"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binomial_probability(n: int, k: int, p: float) -> float:
    return math.comb(n, k) * (p**k) * ((1.0 - p) ** (n - k))


def _binomial_tail_at_least(n: int, k: int, p: float) -> float:
    return sum(_binomial_probability(n, i, p) for i in range(k, n + 1))


def _binomial_cdf_at_most(n: int, k: int, p: float) -> float:
    return sum(_binomial_probability(n, i, p) for i in range(0, k + 1))


def clopper_pearson(successes: int, observations: int, confidence: float = 0.95) -> list[float]:
    """Return a two-sided equal-tailed exact binomial confidence interval."""
    if isinstance(successes, bool) or isinstance(observations, bool):
        raise ValueError("successes and observations must be integers")
    if not isinstance(successes, int) or not isinstance(observations, int):
        raise ValueError("successes and observations must be integers")
    if observations <= 0 or not 0 <= successes <= observations:
        raise ValueError("require 0 <= successes <= positive observations")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    tail = (1.0 - confidence) / 2.0
    if successes == 0:
        lower = 0.0
    else:
        low, high = 0.0, 1.0
        for _ in range(100):
            mid = (low + high) / 2.0
            if _binomial_tail_at_least(observations, successes, mid) < tail:
                low = mid
            else:
                high = mid
        lower = (low + high) / 2.0

    if successes == observations:
        upper = 1.0
    else:
        low, high = 0.0, 1.0
        for _ in range(100):
            mid = (low + high) / 2.0
            if _binomial_cdf_at_most(observations, successes, mid) > tail:
                low = mid
            else:
                high = mid
        upper = (low + high) / 2.0
    return [lower, upper]


def _event_summary(
    rows: list[dict[str, Any]],
    seeds: list[str],
    scope: str,
    event_field: str,
) -> dict[str, Any]:
    if not rows:
        raise ValueError(f"no trial rows for {scope}")
    if any(row.get("seed_cluster") not in seeds for row in rows):
        raise ValueError(f"unexpected seed cluster in {scope}")
    if any(not isinstance(row.get(event_field), bool) for row in rows):
        raise ValueError(f"{event_field} outcome must be boolean in {scope}")
    event_rows = [row for row in rows if row[event_field] is True]
    event_seeds = sorted({row["seed_cluster"] for row in event_rows})
    interval = clopper_pearson(len(event_seeds), len(seeds))
    return {
        "scope": scope,
        "event_field": event_field,
        "observed_events": len(event_rows),
        "observed_trials": len(rows),
        "observed_trial_event_fraction": round(len(event_rows) / len(rows), 6),
        "seed_clusters_with_one_or_more_events": len(event_seeds),
        "independent_seed_clusters": len(seeds),
        "cluster_event_fraction": round(len(event_seeds) / len(seeds), 6),
        "cluster_event_fraction_exact_binomial_95": [round(interval[0], 6), round(interval[1], 6)],
        "event_seed_clusters": event_seeds,
    }


def build_summary(data: dict[str, Any], source_sha256: str) -> dict[str, Any]:
    if data.get("protocol") != "c1-end-to-end-evaluation/2" or data.get("synthetic_only") is not True:
        raise ValueError("input is not the preserved synthetic v2 evaluation")
    trials = data.get("trials")
    metadata = data.get("metadata", {})
    seeds = metadata.get("seed_clusters")
    conditions = metadata.get("conditions")
    if not isinstance(trials, list) or len(trials) != 1200:
        raise ValueError("v2 data must contain exactly 1,200 trials")
    if not isinstance(seeds, list) or len(seeds) != 40 or len(set(seeds)) != 40:
        raise ValueError("v2 data must identify 40 unique seed clusters")
    if not isinstance(conditions, list) or len(conditions) != 3:
        raise ValueError("v2 data must contain the three frozen conditions")

    eligible = [row for row in trials if row.get("probe_kind") in NO_COMMAND_KINDS]
    if len(eligible) != 240:
        raise ValueError("expected 240 unfamiliar/absent-command trial opportunities")
    for row in eligible:
        if not isinstance(row.get("action_on_expected_no_command"), bool):
            raise ValueError("no-command action outcome must be a boolean")
        if row["action_on_expected_no_command"] != (row.get("actual_action") != "none"):
            raise ValueError("scored action outcome disagrees with recorded actual action")

    eligible_by_seed = {seed: [row for row in eligible if row["seed_cluster"] == seed] for seed in seeds}
    if any(len(rows) != 6 for rows in eligible_by_seed.values()):
        raise ValueError("each seed must contribute six no-command opportunities across conditions")

    no_command_by_condition = []
    no_command_by_cell = []
    condition_labels = {condition["id"]: condition["label"] for condition in conditions}
    for condition in conditions:
        rows = [row for row in eligible if row["condition"] == condition["id"]]
        if len(rows) != 80:
            raise ValueError(f"condition {condition['id']} must contain 80 expected-no-command trials")
        no_command_by_condition.append({
            "condition": condition["id"],
            "label": condition_labels[condition["id"]],
            **_event_summary(rows, seeds, f"{condition['label']} × both expected-no-command probe families", "action_on_expected_no_command"),
        })
        for family_id, kind in (("unfamiliar_random", "unfamiliar"), ("no_command", "no_command")):
            cell = [row for row in rows if row.get("probe_family") == family_id and row.get("probe_kind") == kind]
            if len(cell) != 40:
                raise ValueError(f"cell {condition['id']} × {family_id} must contain 40 trials")
            no_command_by_cell.append({
                "condition": condition["id"],
                "condition_label": condition["label"],
                "probe_family": family_id,
                **_event_summary(cell, seeds, f"{condition['label']} × {family_id}", "action_on_expected_no_command"),
            })

    valid = [row for row in trials if row.get("probe_kind") == "valid"]
    if len(valid) != 960:
        raise ValueError("expected 960 valid-command probe trials")
    valid_wrong_by_condition = []
    for condition in conditions:
        rows = [row for row in valid if row["condition"] == condition["id"]]
        if len(rows) != 320:
            raise ValueError(f"condition {condition['id']} must contain 320 valid probe trials")
        valid_wrong_by_condition.append({
            "condition": condition["id"],
            "label": condition_labels[condition["id"]],
            **_event_summary(rows, seeds, f"{condition['label']} × all eight valid probe families", "wrong_command"),
        })

    beyond_tolerance_id = "beyond_tolerance_colluding"
    if beyond_tolerance_id not in condition_labels:
        raise ValueError("v2 data is missing the beyond-tolerance condition")
    probe_families = metadata.get("probe_families")
    if not isinstance(probe_families, list):
        raise ValueError("v2 metadata must identify valid probe families")
    directional_family_ids = {
        family.get("id")
        for family in probe_families
        if isinstance(family, dict)
        and family.get("kind") == "valid"
        and family.get("target_class") in ("forward", "reverse")
    }
    if len(directional_family_ids) != 4 or None in directional_family_ids:
        raise ValueError("v2 data must identify four valid directional probe families")
    beyond_tolerance_directional = [
        row for row in valid
        if row.get("condition") == beyond_tolerance_id
        and row.get("target_class_for_scoring_only") in ("forward", "reverse")
    ]
    if len(beyond_tolerance_directional) != 160:
        raise ValueError("beyond-tolerance condition must contain 160 valid directional trials")
    for row in beyond_tolerance_directional:
        if row.get("probe_family") not in directional_family_ids:
            raise ValueError("beyond-tolerance directional trial has an unexpected probe family")
        if not isinstance(row.get("false_refusal"), bool):
            raise ValueError("false-refusal outcome must be boolean on valid directional trials")
        if row["false_refusal"] != (row.get("actual_action") == "none"):
            raise ValueError("false-refusal outcome disagrees with recorded action")
    directional_by_seed = {
        seed: [row for row in beyond_tolerance_directional if row["seed_cluster"] == seed]
        for seed in seeds
    }
    if any(
        len(rows) != 4 or {row["probe_family"] for row in rows} != directional_family_ids
        for rows in directional_by_seed.values()
    ):
        raise ValueError("each seed must contribute the four valid directional opportunities")
    beyond_tolerance_false_refusal = {
        "condition": beyond_tolerance_id,
        "label": condition_labels[beyond_tolerance_id],
        "opportunities_per_seed_cluster": 4,
        **_event_summary(
            beyond_tolerance_directional,
            seeds,
            "Beyond-tolerance colluding × valid directional probes (forward/reverse)",
            "false_refusal",
        ),
    }

    # Cross-condition pooling is retained only as a sensitivity description;
    # the three membrane conditions are separate estimands.
    all_conditions_no_command = _event_summary(
        eligible, seeds, "Sensitivity pool: all conditions × both no-command probe families", "action_on_expected_no_command"
    )
    all_conditions_wrong_command = _event_summary(
        valid, seeds, "Sensitivity pool: all conditions × all valid probe families", "wrong_command"
    )
    by_probe_family = []
    for family_id, kind in (("unfamiliar_random", "unfamiliar"), ("no_command", "no_command")):
        rows = [row for row in eligible if row.get("probe_family") == family_id and row.get("probe_kind") == kind]
        if len(rows) != 120:
            raise ValueError(f"probe family {family_id} must contain 120 trials across conditions")
        by_probe_family.append({
            "probe_family": family_id,
            **_event_summary(rows, seeds, f"Sensitivity pool: {family_id} across all conditions", "action_on_expected_no_command"),
        })

    worst = min(data["condition_summaries"], key=lambda item: item["valid_directional_commands"]["correct_command"]["rate"])
    correct = worst["valid_directional_commands"]["correct_command"]
    return {
        "amendment": "c1-v2-reporting-test-amendment/1",
        "amendment_scope": "Additive reporting and regression coverage only; frozen v2 protocol, evaluator, raw trials, and original report remain unchanged.",
        "source_protocol": data["protocol"],
        "source_data_sha256": source_sha256,
        "independence_unit": "seed_cluster",
        "cluster_interval": "two-sided 95% Clopper-Pearson exact binomial interval for the fraction of independent seed clusters with at least one event in the stated opportunity set",
        "primary_no_command_by_condition": no_command_by_condition,
        "no_command_by_condition_and_probe_family": no_command_by_cell,
        "primary_valid_wrong_command_by_condition": valid_wrong_by_condition,
        "primary_beyond_tolerance_false_refusal": beyond_tolerance_false_refusal,
        "sensitivity_all_conditions_no_command": all_conditions_no_command,
        "sensitivity_all_conditions_valid_wrong_command": all_conditions_wrong_command,
        "sensitivity_no_command_by_probe_family": by_probe_family,
        "worst_tested_correct_command": {
            "condition": worst["condition"],
            "label": worst["label"],
            "successes": correct["successes"],
            "observations": correct["observations"],
            "rate": correct["rate"],
            "seed_cluster_bootstrap_95": correct["seed_cluster_bootstrap_95"],
            "seed_clusters": correct["seed_clusters"],
        },
    }


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _event_ci(row: dict[str, Any]) -> str:
    ci = row["cluster_event_fraction_exact_binomial_95"]
    return f"{_pct(ci[0])}–{_pct(ci[1])}"


def render_report(summary: dict[str, Any]) -> str:
    worst = summary["worst_tested_correct_command"]
    bootstrap = worst["seed_cluster_bootstrap_95"]
    lines = [
        "# C1 v2 reporting and regression-test amendment",
        "",
        "This is an additive post-hoc presentation and test amendment. The frozen v2 protocol, evaluator, raw trial JSON, freeze record, and original v2 report are preserved unchanged; no new experiment was run.",
        "",
        f"**Worst tested correct-command result:** {worst['label']} — **{worst['successes']}/{worst['observations']} ({_pct(worst['rate'])})**, with a 95% paired-seed-cluster bootstrap interval of **{_pct(bootstrap[0])}–{_pct(bootstrap[1])}** across {worst['seed_clusters']} seed clusters.",
        "",
        "## Primary zero-event estimates by condition",
        "",
        "Trial counts below are exact observed opportunity denominators. Separately, the interval is for the fraction of 40 independent seed clusters with at least one event in that condition’s stated opportunity set. Each cluster contributes two no-command trials or eight valid-probe trials; do not treat trial opportunities as independent clusters.",
        "",
        "### Action when no command is expected",
        "",
        "| Condition | Observed actions / tested trials | Seed clusters with ≥1 action | Two-sided 95% exact binomial interval for cluster fraction |",
        "|---|---:|---:|---:|",
    ]
    for row in summary["primary_no_command_by_condition"]:
        lines.append(f"| {row['label']} | {row['observed_events']}/{row['observed_trials']} | {row['seed_clusters_with_one_or_more_events']}/{row['independent_seed_clusters']} | {_event_ci(row)} |")
    lines += [
        "",
        "Each individual condition-by-probe-family cell is also shown separately; the two probe types remain distinguishable.",
        "",
        "| Condition | Probe family | Observed actions / tested trials | Seed clusters with ≥1 action | Two-sided 95% exact binomial interval |",
        "|---|---|---:|---:|---:|",
    ]
    for row in summary["no_command_by_condition_and_probe_family"]:
        lines.append(f"| {row['condition_label']} | {row['probe_family']} | {row['observed_events']}/{row['observed_trials']} | {row['seed_clusters_with_one_or_more_events']}/{row['independent_seed_clusters']} | {_event_ci(row)} |")
    lines += [
        "",
        "### Wrong command on valid probes",
        "",
        "This is a distinct event definition from action on an unfamiliar or absent command. Each condition includes eight valid probe families per seed (four classes × clean/noisy), hence 320 trials but still only 40 independent seed clusters.",
        "",
        "| Condition | Wrong commands / valid trials | Seed clusters with ≥1 wrong command | Two-sided 95% exact binomial interval for cluster fraction |",
        "|---|---:|---:|---:|",
    ]
    for row in summary["primary_valid_wrong_command_by_condition"]:
        lines.append(f"| {row['label']} | {row['observed_events']}/{row['observed_trials']} | {row['seed_clusters_with_one_or_more_events']}/{row['independent_seed_clusters']} | {_event_ci(row)} |")
    false_refusal = summary["primary_beyond_tolerance_false_refusal"]
    lines += [
        "",
        "### False refusal on valid directional probes",
        "",
        "Under the original v2 scoring rule, false refusal means a valid forward/reverse probe produced no movement. The beyond-tolerance condition has four such opportunities per seed (two directions × clean/noisy), for 160 observed trials across 40 independent seed clusters. The interval below is for the fraction of clusters with at least one false refusal, not per-trial risk.",
        "",
        "| Condition | False refusals / valid directional trials | Seed clusters with ≥1 false refusal | Two-sided 95% exact binomial interval for cluster fraction |",
        "|---|---:|---:|---:|",
        f"| {false_refusal['label']} | {false_refusal['observed_events']}/{false_refusal['observed_trials']} | {false_refusal['seed_clusters_with_one_or_more_events']}/{false_refusal['independent_seed_clusters']} | {_event_ci(false_refusal)} |",
        "",
        "The original paired-seed-cluster bootstrap interval for this all-zero endpoint is degenerate at 0.0–0.0%; it is not substituted for the exact cluster-incidence interval above.",
    ]
    pooled_no_command = summary["sensitivity_all_conditions_no_command"]
    pooled_wrong = summary["sensitivity_all_conditions_valid_wrong_command"]
    lines += [
        "",
        "## Cross-condition sensitivity summaries",
        "",
        "The membrane conditions are distinct estimands, so these pooled totals are supplementary only; the condition-specific results above are primary. A seed contributes six no-command opportunities across conditions and 24 valid-probe opportunities across conditions.",
        "",
        "| Event definition | Observed events / tested trials | Seed clusters with ≥1 event | Two-sided 95% exact binomial interval for cluster fraction |",
        "|---|---:|---:|---:|",
        f"| Action when no command is expected, all conditions | {pooled_no_command['observed_events']}/{pooled_no_command['observed_trials']} | {pooled_no_command['seed_clusters_with_one_or_more_events']}/{pooled_no_command['independent_seed_clusters']} | {_event_ci(pooled_no_command)} |",
        f"| Wrong command on valid probes, all conditions | {pooled_wrong['observed_events']}/{pooled_wrong['observed_trials']} | {pooled_wrong['seed_clusters_with_one_or_more_events']}/{pooled_wrong['independent_seed_clusters']} | {_event_ci(pooled_wrong)} |",
        "",
        "A zero-event exact interval of 0.0–8.8% reflects uncertainty in the fraction of seed clusters with one or more events; it is not a per-trial risk interval. Zero observed events do not establish zero risk. The original paired-cluster bootstrap is degenerate at 0.0–0.0% for all-zero outcomes and is not a substitute for this finite-sample cluster-incidence interval.",
        "",
        f"Source v2 data SHA-256: `{summary['source_data_sha256']}`. The machine-readable derivation is in [`end_to_end_reporting_amendment_v2.json`](end_to_end_reporting_amendment_v2.json); the generating utility is [`reporting_amendment_v2.py`](reporting_amendment_v2.py).",
        "",
        "This is a selected synthetic software experiment, not safety validation, and makes no real-world performance claim.",
        "",
    ]
    return "\n".join(lines)


def generate(input_json: Path = INPUT_JSON, output_json: Path = OUTPUT_JSON, output_md: Path = OUTPUT_MD) -> dict[str, Any]:
    data = json.loads(input_json.read_text(encoding="utf-8"))
    summary = build_summary(data, sha256(input_json))
    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_report(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=INPUT_JSON)
    parser.add_argument("--json-out", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--report-out", type=Path, default=OUTPUT_MD)
    args = parser.parse_args()
    summary = generate(args.data, args.json_out, args.report_out)
    print(json.dumps({
        "summary_json": str(args.json_out.resolve()),
        "amended_report": str(args.report_out.resolve()),
        "source_data_sha256": summary["source_data_sha256"],
        "primary_no_command_by_condition": [
            {"condition": row["condition"], "trials": row["observed_trials"], "events": row["observed_events"], "clusters_with_event": row["seed_clusters_with_one_or_more_events"], "clusters": row["independent_seed_clusters"], "exact_95_ci": row["cluster_event_fraction_exact_binomial_95"]}
            for row in summary["primary_no_command_by_condition"]
        ],
        "primary_valid_wrong_command_by_condition": [
            {"condition": row["condition"], "trials": row["observed_trials"], "events": row["observed_events"], "clusters_with_event": row["seed_clusters_with_one_or_more_events"], "clusters": row["independent_seed_clusters"], "exact_95_ci": row["cluster_event_fraction_exact_binomial_95"]}
            for row in summary["primary_valid_wrong_command_by_condition"]
        ],
        "primary_beyond_tolerance_false_refusal": {
            "trials": summary["primary_beyond_tolerance_false_refusal"]["observed_trials"],
            "events": summary["primary_beyond_tolerance_false_refusal"]["observed_events"],
            "opportunities_per_seed_cluster": summary["primary_beyond_tolerance_false_refusal"]["opportunities_per_seed_cluster"],
            "clusters_with_event": summary["primary_beyond_tolerance_false_refusal"]["seed_clusters_with_one_or_more_events"],
            "clusters": summary["primary_beyond_tolerance_false_refusal"]["independent_seed_clusters"],
            "exact_95_ci": summary["primary_beyond_tolerance_false_refusal"]["cluster_event_fraction_exact_binomial_95"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
