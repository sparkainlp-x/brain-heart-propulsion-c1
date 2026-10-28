#!/usr/bin/env python3
"""Corrected frozen local C1 end-to-end evaluation v2."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from brain_propulsion import C1Actuator, ROOT
from propulsion.linked import BRAIN_N, LinkedSystem, noisy, rand_field

PROTOCOL = ROOT / "END_TO_END_PROTOCOL_V2.md"
HASH_MANIFEST = ROOT / "END_TO_END_PROTOCOL_V2.sha256"
FREEZE_RECORD = ROOT / "END_TO_END_FREEZE_V2.json"
MEMBRANE_RUNNER = ROOT / "e2e_membrane_batch.js"
OUTPUT_JSON = ROOT / "end_to_end_evaluation_v2.json"
OUTPUT_MD = ROOT / "end_to_end_report_v2.md"
SEED_COUNT = 40
HEART_STEPS = 2_000
BOOTSTRAP_REPS = 2_000
BOOTSTRAP_SEED = 20261027
CLASSES = ("forward", "reverse", "hold", "rest")
RESPONSE_CATEGORIES = (*CLASSES, "reject")

CONDITIONS = (
    {"id": "clean", "label": "Clean", "faults": {"mode": "collude"}},
    {"id": "within_tolerance_colluding", "label": "Within-tolerance colluding", "faults": {"sensory": 1, "columns": 1, "mode": "collude"}},
    {"id": "beyond_tolerance_colluding", "label": "Beyond-tolerance colluding", "faults": {"sensory": 2, "mode": "collude"}},
)
PROBE_FAMILIES = tuple(
    [{"id": f"clean_{c}", "kind": "valid", "quality": "clean", "target_class": c, "sigma": 0.0} for c in CLASSES]
    + [{"id": f"noisy_{c}", "kind": "valid", "quality": "noisy_sigma_0.15", "target_class": c, "sigma": 0.15} for c in CLASSES]
    + [
        {"id": "unfamiliar_random", "kind": "unfamiliar", "quality": "random_ood", "target_class": None, "sigma": None},
        {"id": "no_command", "kind": "no_command", "quality": "absent", "target_class": None, "sigma": None},
    ]
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict[str, str]:
    if not HASH_MANIFEST.is_file():
        raise RuntimeError("frozen hash manifest is missing")
    out: dict[str, str] = {}
    for line in HASH_MANIFEST.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            out[parts[1].strip()] = parts[0]
    return out


def verify_frozen_files() -> dict[str, str]:
    files = (
        PROTOCOL,
        Path(__file__).resolve(),
        MEMBRANE_RUNNER,
        ROOT / "brain_propulsion.py",
        ROOT / "brain.js",
        ROOT / "game.js",
        ROOT / "baselines.js",
        ROOT / "stats.js",
        ROOT / "brain-i18n.js",
        ROOT / "propulsion" / "linked.py",
        ROOT / "tests" / "test_c1_connector.py",
        ROOT / "tests" / "test_e2e_eval.py",
        ROOT / "tests" / "test_e2e_v2_pairing.py",
    )
    manifest = load_manifest()
    verified: dict[str, str] = {}
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        expected = manifest.get(name)
        if expected is None:
            raise RuntimeError(f"no frozen SHA-256 recorded for {name}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"frozen file hash mismatch: {name}")
        verified[name] = actual
    record = json.loads(FREEZE_RECORD.read_text(encoding="utf-8"))
    if record.get("protocol") != "c1-end-to-end-evaluation/2":
        raise RuntimeError("freeze record is not for corrected protocol v2")
    if record.get("status") != "FROZEN_BEFORE_DATA_GENERATION":
        raise RuntimeError("freeze record does not attest pre-data freeze")
    if record.get("data_generated_at_utc") is not None:
        raise RuntimeError("freeze record does not mark pre-data state")
    if record.get("manifest_sha256") != sha256(HASH_MANIFEST):
        raise RuntimeError("freeze manifest SHA-256 mismatch")
    for name, digest in verified.items():
        if record.get("sha256", {}).get(name) != digest:
            raise RuntimeError(f"freeze record mismatch for {name}")
    return verified


def wilson(successes: int, n: int) -> list[float] | None:
    if n <= 0:
        return None
    z = 1.959963984540054
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [round(max(0.0, center - half), 6), round(min(1.0, center + half), 6)]


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        raise ValueError("percentile requires values")
    pos = (len(sorted_values) - 1) * p
    low, high = int(math.floor(pos)), int(math.ceil(pos))
    return sorted_values[low] if low == high else sorted_values[low] * (high - pos) + sorted_values[high] * (pos - low)


def cluster_interval(
    rows: list[dict[str, Any]],
    seeds: list[str],
    draws: list[list[int]],
    numerator: Callable[[dict[str, Any]], bool],
    denominator: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    grouped = {seed: [] for seed in seeds}
    for row in rows:
        grouped[row["seed_cluster"]].append(row)
    counts = {
        seed: (
            sum(1 for row in grouped[seed] if numerator(row)),
            sum(1 for row in grouped[seed] if denominator(row)),
        )
        for seed in seeds
    }
    successes = sum(k for k, _ in counts.values())
    observations = sum(n for _, n in counts.values())
    if observations == 0:
        raise ValueError("metric has no denominator observations")
    rates = []
    for draw in draws:
        k = sum(counts[seeds[index]][0] for index in draw)
        n = sum(counts[seeds[index]][1] for index in draw)
        if n:
            rates.append(k / n)
    rates.sort()
    result: dict[str, Any] = {
        "successes": successes,
        "observations": observations,
        "rate": round(successes / observations, 6),
        "seed_clusters": len(seeds),
        "seed_cluster_bootstrap_95": [round(percentile(rates, .025), 6), round(percentile(rates, .975), 6)],
        "bootstrap_replicates": len(draws),
    }
    if all(n <= 1 for _, n in counts.values()) and observations == len(seeds):
        result["independent_seed_wilson_95"] = wilson(successes, observations)
    return result


def metric(rows: list[dict[str, Any]], seeds: list[str], draws: list[list[int]], predicate: Callable[[dict[str, Any]], bool], denominator: Callable[[dict[str, Any]], bool] | None = None) -> dict[str, Any]:
    return cluster_interval(rows, seeds, draws, predicate, denominator or (lambda _row: True))


def make_probe(system: LinkedSystem, family: dict[str, Any], seed_cluster: str) -> list[complex] | None:
    if family["kind"] == "no_command":
        return None
    rng = random.Random(f"c1-e2e-v2-classifier-input::{seed_cluster}::{family['id']}")
    if family["kind"] == "unfamiliar":
        return rand_field(BRAIN_N, rng)
    template = system.brain.patterns[CLASSES.index(family["target_class"])]
    return noisy(template, float(family["sigma"]), rng) if family["sigma"] else list(template)


def event_order_for_seed(seed_cluster: str) -> list[int]:
    """Shuffle episode-to-family assignment once per seed, shared across conditions."""
    order = list(range(len(PROBE_FAMILIES)))
    random.Random(f"c1-e2e-v2-event-pairing::{seed_cluster}").shuffle(order)
    return order


def action_from_displacement(displacement: float) -> str:
    if displacement > 1e-12:
        return "forward"
    if displacement < -1e-12:
        return "reverse"
    return "none"


def score_after_actuation(raw: dict[str, Any], family: dict[str, Any]) -> dict[str, Any]:
    """Add scoring labels after label-blind classification, gate, and motion."""
    target = family["target_class"]
    action = raw["actual_action"]
    correct_command = correct_no_action = wrong_command = false_refusal = action_on_expected_no_command = False
    if family["kind"] == "valid":
        if target in ("forward", "reverse"):
            if action == target:
                outcome, correct_command = "correct_command", True
            elif action == "none":
                outcome, false_refusal = "false_refusal", True
            else:
                outcome, wrong_command = "wrong_command", True
        elif action == "none":
            outcome, correct_no_action = "correct_no_action", True
        else:
            outcome, wrong_command = "wrong_command", True
        expected_action = target if target in ("forward", "reverse") else "none"
    else:
        expected_action = "none"
        if action == "none":
            outcome = "no_action"
        else:
            outcome, action_on_expected_no_command = "action_on_expected_no_command", True
    return {
        **raw,
        "probe_family": family["id"],
        "probe_kind": family["kind"],
        "probe_quality": family["quality"],
        "target_class_for_scoring_only": target,
        "expected_action_for_scoring_only": expected_action,
        "scored_outcome": outcome,
        "correct_command": correct_command,
        "correct_no_action": correct_no_action,
        "wrong_command": wrong_command,
        "false_refusal": false_refusal,
        "action_on_expected_no_command": action_on_expected_no_command,
    }


def run_membrane_batch(seeds: list[str]) -> tuple[dict[tuple[str, str], list[bool]], str]:
    runs = [
        {"runId": f"{seed}::{condition['id']}", "seed": seed, "faults": condition["faults"]}
        for seed in seeds for condition in CONDITIONS
    ]
    proc = subprocess.run(
        ["node", str(MEMBRANE_RUNNER)], input=json.dumps({"runs": runs}), text=True,
        capture_output=True, cwd=ROOT, timeout=900, check=False,
    )
    if proc.returncode:
        raise RuntimeError(f"membrane batch failed: {proc.stderr.strip()}")
    payload = json.loads(proc.stdout)
    if payload.get("protocol") != "c1-e2e-membrane-events/1" or payload.get("synthetic") is not True:
        raise RuntimeError("membrane batch response failed validation")
    if payload.get("episodesPerRun") != len(PROBE_FAMILIES):
        raise RuntimeError("membrane batch episode count differs from frozen protocol")
    by_run: dict[tuple[str, str], list[bool]] = {}
    for run in payload.get("runs", []):
        seed, condition_id = run["runId"].split("::", 1)
        events = run.get("membraneEvents")
        if len(events) != len(PROBE_FAMILIES) or any(not isinstance(v, bool) for v in events):
            raise RuntimeError("invalid membrane event list")
        by_run[(seed, condition_id)] = events
    if len(by_run) != len(runs):
        raise RuntimeError("membrane batch omitted or duplicated runs")
    return by_run, payload["nodeVersion"]


def build_confusion(trials: list[dict[str, Any]], seeds: list[str], draws: list[list[int]]) -> list[dict[str, Any]]:
    result = []
    for condition in CONDITIONS:
        for family in PROBE_FAMILIES:
            if family["kind"] != "valid":
                continue
            rows = [r for r in trials if r["condition"] == condition["id"] and r["probe_family"] == family["id"]]
            entry = {"condition": condition["id"], "probe_family": family["id"], "quality": family["quality"], "target_class": family["target_class"], "predictions": {}}
            for category in RESPONSE_CATEGORIES:
                entry["predictions"][category] = metric(rows, seeds, draws, lambda r, c=category: r["classifier_prediction"] == c)
            result.append(entry)
    return result


def build_per_class_actions(trials: list[dict[str, Any]], seeds: list[str], draws: list[list[int]]) -> list[dict[str, Any]]:
    result = []
    for condition in CONDITIONS:
        for family in PROBE_FAMILIES:
            if family["kind"] != "valid":
                continue
            rows = [r for r in trials if r["condition"] == condition["id"] and r["probe_family"] == family["id"]]
            target = family["target_class"]
            directional = target in ("forward", "reverse")
            result.append({
                "condition": condition["id"],
                "probe_family": family["id"],
                "quality": family["quality"],
                "target_class": target,
                "correct_command": metric(rows, seeds, draws, lambda r: r["correct_command"], lambda r: r["target_class_for_scoring_only"] in ("forward", "reverse")) if directional else None,
                "correct_no_action": metric(rows, seeds, draws, lambda r: r["correct_no_action"]) if not directional else None,
                "wrong_command": metric(rows, seeds, draws, lambda r: r["wrong_command"]),
                "false_refusal": metric(rows, seeds, draws, lambda r: r["false_refusal"]) if directional else None,
                "classifier_not_correct_class": metric(rows, seeds, draws, lambda r: r["classifier_prediction"] != target),
            })
    return result


def build_condition_summaries(trials: list[dict[str, Any]], seeds: list[str], draws: list[list[int]]) -> list[dict[str, Any]]:
    result = []
    for condition in CONDITIONS:
        rows = [r for r in trials if r["condition"] == condition["id"]]
        valid = [r for r in rows if r["probe_kind"] == "valid"]
        directional = [r for r in valid if r["target_class_for_scoring_only"] in ("forward", "reverse")]
        hold_rest = [r for r in valid if r["target_class_for_scoring_only"] in ("hold", "rest")]
        unfamiliar = [r for r in rows if r["probe_family"] == "unfamiliar_random"]
        no_command = [r for r in rows if r["probe_family"] == "no_command"]
        expected_no_command = unfamiliar + no_command
        result.append({
            "condition": condition["id"],
            "label": condition["label"],
            "trials": len(rows),
            "valid_named_inputs": {
                "trials": len(valid),
                "wrong_command": metric(valid, seeds, draws, lambda r: r["wrong_command"]),
                "correct_end_to_end_outcome": metric(valid, seeds, draws, lambda r: r["correct_command"] or r["correct_no_action"]),
            },
            "valid_directional_commands": {
                "trials": len(directional),
                "correct_command": metric(directional, seeds, draws, lambda r: r["correct_command"]),
                "wrong_command": metric(directional, seeds, draws, lambda r: r["wrong_command"]),
                "false_refusal": metric(directional, seeds, draws, lambda r: r["false_refusal"]),
            },
            "valid_hold_rest": {
                "trials": len(hold_rest),
                "correct_no_action": metric(hold_rest, seeds, draws, lambda r: r["correct_no_action"]),
                "wrong_command": metric(hold_rest, seeds, draws, lambda r: r["wrong_command"]),
                "classifier_not_correct_class": metric(hold_rest, seeds, draws, lambda r: r["classifier_prediction"] != r["target_class_for_scoring_only"]),
            },
            "expected_no_command": {
                "trials": len(expected_no_command),
                "action_on_expected_no_command": metric(expected_no_command, seeds, draws, lambda r: r["action_on_expected_no_command"]),
                "unfamiliar_random": metric(unfamiliar, seeds, draws, lambda r: r["action_on_expected_no_command"]),
                "no_command": metric(no_command, seeds, draws, lambda r: r["action_on_expected_no_command"]),
            },
        })
    return result


def build_seed_cluster_counts(trials: list[dict[str, Any]], seeds: list[str]) -> list[dict[str, Any]]:
    result = []
    for condition in CONDITIONS:
        for seed in seeds:
            rows = [r for r in trials if r["condition"] == condition["id"] and r["seed_cluster"] == seed]
            valid = [r for r in rows if r["probe_kind"] == "valid"]
            directional = [r for r in valid if r["target_class_for_scoring_only"] in ("forward", "reverse")]
            unfamiliar = [r for r in rows if r["probe_family"] == "unfamiliar_random"]
            no_command = [r for r in rows if r["probe_family"] == "no_command"]
            result.append({
                "condition": condition["id"],
                "seed_cluster": seed,
                "trials": len(rows),
                "correct_commands": sum(r["correct_command"] for r in directional),
                "wrong_commands_on_valid": sum(r["wrong_command"] for r in valid),
                "false_refusals_on_directional": sum(r["false_refusal"] for r in directional),
                "actions_on_unfamiliar_expected_no_command": sum(r["action_on_expected_no_command"] for r in unfamiliar),
                "actions_on_absent_expected_no_command": sum(r["action_on_expected_no_command"] for r in no_command),
            })
    return result


def format_metric(m: dict[str, Any]) -> str:
    paired = m["seed_cluster_bootstrap_95"]
    text = f"{m['successes']}/{m['observations']} ({m['rate'] * 100:.1f}%; 95% paired-seed bootstrap {paired[0] * 100:.1f}–{paired[1] * 100:.1f}%"
    wilson_ci = m.get("independent_seed_wilson_95")
    if wilson_ci is not None:
        text += f"; 40-seed Wilson {wilson_ci[0] * 100:.1f}–{wilson_ci[1] * 100:.1f}%"
    return text + ")"


def render_report(report: dict[str, Any]) -> str:
    lines = [
        "# C1 end-to-end evaluation (corrected frozen protocol v2)",
        "",
        "This is a selected synthetic software experiment, not safety validation. The membrane model and classifier receive separate generated inputs. V1 is preserved for audit, but its fixed episode-index pairing aliased some episode outputs to probe families; v2 uses a seed-specific shuffled pairing shared across conditions. Target labels are attached only after the resettable, label-blind gate and simulated ring action for scoring.",
        "",
        f"- Protocol SHA-256: `{report['frozen_hashes']['END_TO_END_PROTOCOL_V2.md']}`",
        f"- Evaluator SHA-256: `{report['frozen_hashes']['evaluate_c1_e2e_v2.py']}`",
        f"- Protocol frozen at: {report['freeze_record']['frozen_at_utc']}",
        f"- Evaluation generated at: {report['metadata']['generated_at_utc']}",
        f"- Design: 40 paired seed clusters × 3 membrane conditions × 10 probe families = {len(report['trials'])} trials; the same shuffled episode-to-family assignment is used across conditions within each seed.",
        f"- Frozen classifier calibration: tau {report['metadata']['classifier_calibration']['tau']:.3f}; Youden J {report['metadata']['classifier_calibration']['youden_j']:.3f}.",
        "",
        f"**Worst tested condition by correct-command rate:** {min(report['condition_summaries'], key=lambda s: s['valid_directional_commands']['correct_command']['rate'])['label']} — {format_metric(min(report['condition_summaries'], key=lambda s: s['valid_directional_commands']['correct_command']['rate'])['valid_directional_commands']['correct_command'])}.",
        "",
        "## Distinct end-to-end outcomes",
        "",
        "Correct command, wrong command, action when no command is expected, and false refusal are separate measures. False refusal applies to valid forward/reverse probes that result in no movement. For hold/rest, no movement is correct; classifier misrecognition and unexpected movement are reported separately.",
        "",
        "| Membrane condition | Correct command on valid forward/reverse | Wrong command on all valid probes | False refusal on valid directional probes | Action on unfamiliar input (no command expected) | Action on absent command |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for summary in report["condition_summaries"]:
        d = summary["valid_directional_commands"]
        n = summary["expected_no_command"]
        lines.append(
            f"| {summary['label']} | {format_metric(d['correct_command'])} | {format_metric(summary['valid_named_inputs']['wrong_command'])} | {format_metric(d['false_refusal'])} | {format_metric(n['unfamiliar_random'])} | {format_metric(n['no_command'])} |"
        )
    lines += [
        "",
        "All intervals use the paired seed-cluster design; pooled rates resample whole clusters (2,000 fixed bootstrap replicates). Single-trial-per-seed cells also show a 40-seed Wilson interval. A 0/n observation is not zero risk: the paired bootstrap can be degenerate when all observed clusters are zero, so read the finite-sample Wilson upper bound too.",
        "",
        "## Per-class classifier confusion and end-to-end outcomes",
        "",
        "`F/R/H/Rest/X` are classifier predictions `forward/reverse/hold/rest/reject`; each cell is out of 40 independent seed clusters. `Correct cmd` applies to forward/reverse; `Correct none` applies to hold/rest.",
        "",
        "| Condition | Probe quality | Target | F | R | H | Rest | X | Correct cmd | Correct none | Wrong cmd | False refusal |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    actions = {(x["condition"], x["probe_family"]): x for x in report["per_class_actions"]}
    for cell in report["classifier_confusion"]:
        action = actions[(cell["condition"], cell["probe_family"])]
        pred = cell["predictions"]
        get = lambda key: pred[key]["successes"]
        correct_cmd = action["correct_command"]["successes"] if action["correct_command"] else "—"
        correct_none = action["correct_no_action"]["successes"] if action["correct_no_action"] else "—"
        false_refusal = action["false_refusal"]["successes"] if action["false_refusal"] else "—"
        false_refusal_text = "—" if false_refusal == "—" else f"{false_refusal}/40"
        lines.append(
            f"| {cell['condition']} | {cell['quality']} | {cell['target_class']} | {get('forward')} | {get('reverse')} | {get('hold')} | {get('rest')} | {get('reject')} | {correct_cmd if correct_cmd == '—' else f'{correct_cmd}/40'} | {correct_none if correct_none == '—' else f'{correct_none}/40'} | {action['wrong_command']['successes']}/40 | {false_refusal_text} |"
        )
    lines += [
        "",
        "The JSON also includes per-class confidence intervals, per-seed cluster counts, classifier exceptions, and all 1,200 raw trial records.",
        "",
        "## Interpretation boundary",
        "",
        "The red panel in the supplied diagram and the prior `EVALUATION.md` are membrane-only fault-test results; they are not end-to-end action rates. This report scores the separate combined gate through the in-memory clock and ring. The batch helper returns membrane event bits only, never planted/truth labels. Each trial resets drive, position, phases, and clock; rejected, unknown, malformed, missing, or exceptional classifier output maps to `no_command`.",
        "",
        "This is not safety validation and makes no safety, robustness, biological, medical, hardware, or real-world performance claim. The diagram labels the logic as not a safety guarantee.",
        "",
        "See [`END_TO_END_PROTOCOL_V2.md`](END_TO_END_PROTOCOL_V2.md), [`end_to_end_evaluation_v2.json`](end_to_end_evaluation_v2.json), the preserved v1 report [`end_to_end_report.md`](end_to_end_report.md), and the separate prior membrane-only [`EVALUATION.md`](EVALUATION.md).",
        "",
    ]
    return "\n".join(lines)


def generate() -> tuple[dict[str, Any], str]:
    frozen_hashes = verify_frozen_files()
    freeze_record = json.loads(FREEZE_RECORD.read_text(encoding="utf-8"))
    if OUTPUT_JSON.exists() or OUTPUT_MD.exists():
        raise FileExistsError("end-to-end outputs already exist; refusing to overwrite")

    seeds = [f"c1-e2e-v2-seed-{i:03d}" for i in range(1, SEED_COUNT + 1)]
    membrane_events, node_version = run_membrane_batch(seeds)
    classifier = LinkedSystem(seed=42)
    tau, youden_j = classifier.calibrate()
    actuator = C1Actuator()  # Reused across trials; apply_classifier resets before every episode.
    trials: list[dict[str, Any]] = []

    for seed in seeds:
        episode_order = event_order_for_seed(seed)
        for condition in CONDITIONS:
            events = membrane_events[(seed, condition["id"])]
            for index, family in enumerate(PROBE_FAMILIES):
                episode_index = episode_order[index]
                def classifier_call(fam=family, cluster=seed):
                    if fam["kind"] == "no_command":
                        return ("no_command", None, None)
                    probe = make_probe(classifier, fam, cluster)
                    return classifier.brain.decide(probe)

                action_result = actuator.apply_classifier(events[episode_index], classifier_call, HEART_STEPS)
                actual_action = action_from_displacement(action_result["propulsion"]["displacement"])
                if (actual_action == "forward" and action_result["drive"] != 1) or (actual_action == "reverse" and action_result["drive"] != -1):
                    raise RuntimeError("ring displacement sign disagrees with simulated drive")
                classifier_prediction = (
                    action_result["classifier_response"]
                    if action_result["classifier_decision"] == "accept"
                    else ("no_command" if family["kind"] == "no_command" else "reject")
                )
                raw = {
                    "seed_cluster": seed,
                    "condition": condition["id"],
                    "membrane_episode_index": episode_index,
                    "membrane_event": action_result["membrane_event"],
                    "classifier_decision": action_result["classifier_decision"],
                    "classifier_response": action_result["classifier_response"],
                    "classifier_prediction": classifier_prediction,
                    "classifier_error_type": action_result.get("classifier_error_type"),
                    "combined_gate_passed": action_result["combined_gate_passed"],
                    "proposed_drive": action_result["proposed_drive"],
                    "actual_drive": action_result["drive"],
                    "actual_displacement": action_result["propulsion"]["displacement"],
                    "actual_action": actual_action,
                    "trial_reset_applied": action_result["trial_reset_applied"],
                    "heart_ticks": action_result["heart"]["ticks"],
                    "steps": HEART_STEPS,
                }
                # Target labels enter only after the decision, gate, and motion.
                trials.append(score_after_actuation(raw, family))

    expected = SEED_COUNT * len(CONDITIONS) * len(PROBE_FAMILIES)
    if len(trials) != expected:
        raise RuntimeError(f"expected {expected} trials, received {len(trials)}")
    rng = random.Random(BOOTSTRAP_SEED)
    draws = [[rng.randrange(SEED_COUNT) for _ in range(SEED_COUNT)] for _ in range(BOOTSTRAP_REPS)]
    report: dict[str, Any] = {
        "protocol": "c1-end-to-end-evaluation/2",
        "synthetic_only": True,
        "frozen_hashes": frozen_hashes,
        "freeze_record": freeze_record,
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "node_version": node_version,
            "independent_seed_clusters": SEED_COUNT,
            "seed_clusters": seeds,
            "conditions": list(CONDITIONS),
            "probe_families": list(PROBE_FAMILIES),
            "total_trials": len(trials),
            "bootstrap_replicates": BOOTSTRAP_REPS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "intervals": {
                "per_cell": "95% Wilson over 40 independent seed observations plus paired seed-cluster bootstrap",
                "pooled": "95% percentile intervals from resampling entire paired seed clusters",
            },
            "classifier_calibration": {"seed": 42, "tau": tau, "youden_j": youden_j, "held_fixed": True},
            "actuator": {"reset_each_trial": True, "invalid_rejected_missing_exception_output": "no_command"},
            "separate_input_namespaces": {"membrane": "c1-e2e-v2-seed-###", "classifier_probe_rng": "c1-e2e-v2-classifier-input::<seed>::<family>", "event_pairing": "c1-e2e-v2-event-pairing::<seed>"},
            "event_pairing": "seed-specific permutation of episodes 0-9, reused across all conditions within each seed cluster",
            "ground_truth_use": "scoring only, attached after the actuator result",
            "membrane_batch_truth_fields_returned": False,
            "classifier_error_count": sum(r["classifier_error_type"] is not None for r in trials),
        },
        "condition_summaries": build_condition_summaries(trials, seeds, draws),
        "classifier_confusion": build_confusion(trials, seeds, draws),
        "per_class_actions": build_per_class_actions(trials, seeds, draws),
        "per_seed_cluster_counts": build_seed_cluster_counts(trials, seeds),
        "trials": trials,
        "report_file": OUTPUT_MD.name,
    }
    return report, render_report(report)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen local C1 end-to-end evaluation")
    parser.add_argument("--validate-only", action="store_true", help="verify hashes without generating evaluation data")
    args = parser.parse_args()
    try:
        hashes = verify_frozen_files()
        if args.validate_only:
            print(json.dumps({"valid": True, "hashes": hashes}, indent=2))
            return 0
        if OUTPUT_JSON.exists() or OUTPUT_MD.exists():
            raise FileExistsError("end-to-end output exists; refusing to overwrite")
        report, markdown = generate()
        OUTPUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        OUTPUT_MD.write_text(markdown, encoding="utf-8")
        print(json.dumps({
            "json": str(OUTPUT_JSON),
            "report": str(OUTPUT_MD),
            "trials": len(report["trials"]),
            "frozen_hashes": report["frozen_hashes"],
            "generated_at_utc": report["metadata"]["generated_at_utc"],
            "classifier_error_count": report["metadata"]["classifier_error_count"],
        }, indent=2))
        return 0
    except Exception as exc:
        print(f"evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
