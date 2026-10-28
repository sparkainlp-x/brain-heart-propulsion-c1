"""C1 software-only connector composing two synthetic brain stages.

The membrane model emits a permission event; the separately generated
propulsion-toy classifier input supplies a named response. Every actuator
trial resets to zero drive. Invalid, rejected, absent, or exceptional
classifier outputs become no-command. This remains an in-memory toy.
"""
from __future__ import annotations

import json
import math
import random
import subprocess
from pathlib import Path
from typing import Any, Callable

from propulsion.linked import (
    BRAIN_N,
    HEART_PERIOD_STEPS,
    RING_N,
    Brain,
    HeartClock,
    LinkedSystem,
    PropulsionRing,
    noisy,
    rand_field,
)

ROOT = Path(__file__).resolve().parent
BRAIN_RUNNER = ROOT / "brain_trial.js"
PROBE_NAMES = ("forward", "reverse", "hold", "rest", "random", "no_command")
MAX_TOTAL_STEPS = 100_000
MAX_NOISE_SIGMA = 1.0


def run_brain_event(seed: str = "c1-demo", faults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run one deterministic synthetic membrane-brain episode."""
    if not isinstance(seed, str) or not 1 <= len(seed) <= 40:
        raise ValueError("seed must be a string of 1 to 40 characters")
    if faults is not None and not isinstance(faults, dict):
        raise ValueError("faults must be a dictionary")

    request = {"seed": seed, "faults": faults or {}}
    try:
        proc = subprocess.run(
            ["node", str(BRAIN_RUNNER)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=ROOT,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Node.js is required to run the local brain simulation") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"synthetic membrane-brain runner failed: {proc.stderr.strip()}")
    try:
        payload = json.loads(proc.stdout)
        brain = payload["brain"]
        event = brain["event"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError("synthetic membrane-brain runner returned an invalid response") from exc
    if payload.get("synthetic") is not True or not isinstance(event, bool):
        raise RuntimeError("synthetic membrane-brain response failed validation")
    return brain


def normalize_classifier_output(decision: Any, response: Any) -> tuple[str, str | None]:
    """Accept only a known mapped response; all other classifier states abstain."""
    if decision == "accept" and isinstance(response, str) and response in Brain.RESPONSE_TO_DRIVE:
        return "accept", response
    return "no_command", None


class C1Actuator:
    """Stateless-per-trial simulated actuator; every call starts from zero drive."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Clear command, clock, ring position, and phases for a fresh episode."""
        self.clock = HeartClock(period_steps=HEART_PERIOD_STEPS)
        self.ring = PropulsionRing(n=RING_N)
        self.ring.set_drive(0)
        self.last_drive = 0
        self.last_decision = "no_command"
        self.last_response = None

    def apply(
        self,
        membrane_event: Any,
        classifier_decision: Any,
        classifier_response: Any,
        total_steps: int = 2_000,
    ) -> dict[str, Any]:
        """Reset, normalize observed gate outputs, and simulate one trial."""
        self.reset()
        if isinstance(total_steps, bool) or not isinstance(total_steps, int) or not 0 <= total_steps <= MAX_TOTAL_STEPS:
            raise ValueError(f"total_steps must be an integer between 0 and {MAX_TOTAL_STEPS}")
        event = membrane_event if isinstance(membrane_event, bool) else False
        decision, response = normalize_classifier_output(classifier_decision, classifier_response)
        proposed_drive = Brain.RESPONSE_TO_DRIVE[response] if decision == "accept" and response is not None else 0
        combined_gate_passed = bool(event and decision == "accept")
        drive = proposed_drive if combined_gate_passed else 0

        self.ring.set_drive(drive)
        start = self.ring.position
        for _ in range(total_steps):
            if self.clock.step():
                self.ring.tick_move()
        displacement = self.ring.position - start
        raw_sensor = self.ring.sensor()
        self.last_drive = drive
        self.last_decision = decision
        self.last_response = response
        sensor = {
            "k_est": raw_sensor["k_est"],
            "coherence": raw_sensor["coherence"],
            "mean_gradient": raw_sensor["mean_gradient"],
        }
        return {
            "membrane_event": event,
            "classifier_decision": decision,
            "classifier_response": response,
            "combined_gate_passed": combined_gate_passed,
            "proposed_drive": proposed_drive,
            "drive": drive,
            "trial_reset_applied": True,
            "heart": {
                "is_clock_not_heartbeat": True,
                "period_steps": self.clock.period,
                "ticks": self.clock.ticks,
            },
            "propulsion": {
                "ring_sites": self.ring.n,
                "total_steps": total_steps,
                "start_position": start,
                "final_position": self.ring.position,
                "displacement": displacement,
            },
            "sensor": sensor,
        }

    def apply_classifier(
        self,
        membrane_event: Any,
        classifier_call: Callable[[], Any],
        total_steps: int = 2_000,
    ) -> dict[str, Any]:
        """Reset before classification; exceptions/malformed returns abstain."""
        self.reset()
        try:
            output = classifier_call()
        except Exception as exc:
            result = self.apply(membrane_event, "no_command", None, total_steps)
            result["classifier_error_type"] = type(exc).__name__
            return result
        if not isinstance(output, (tuple, list)) or len(output) != 3:
            result = self.apply(membrane_event, "no_command", None, total_steps)
            result["classifier_error_type"] = "malformed_output"
            return result
        decision, response, _winner = output
        result = self.apply(membrane_event, decision, response, total_steps)
        result["classifier_error_type"] = None
        return result


def apply_composite_gate(
    membrane_event: Any,
    classifier_decision: Any = None,
    classifier_response: Any = None,
    total_steps: int = 2_000,
) -> dict[str, Any]:
    """Apply two observed outputs; every call gets a fresh zeroed actuator."""
    return C1Actuator().apply(membrane_event, classifier_decision, classifier_response, total_steps)


def _make_classifier_probe(system: LinkedSystem, probe_name: str, noise_sigma: float) -> list[complex]:
    if probe_name == "random":
        return rand_field(BRAIN_N, random.Random(7))
    index = ("forward", "reverse", "hold", "rest").index(probe_name)
    probe = system.brain.patterns[index]
    if noise_sigma:
        probe = noisy(probe, noise_sigma, random.Random(99))
    return probe


def run_c1_trial(
    probe_name: str,
    *,
    seed: str = "c1-demo",
    total_steps: int = 2_000,
    noise_sigma: float = 0.0,
    faults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run two separate synthetic inputs through the resettable C1 gate."""
    if not isinstance(probe_name, str) or probe_name not in PROBE_NAMES:
        raise ValueError(f"probe_name must be one of: {', '.join(PROBE_NAMES)}")
    if isinstance(seed, str) is False or not 1 <= len(seed) <= 40:
        raise ValueError("seed must be a string of 1 to 40 characters")
    if faults is not None and not isinstance(faults, dict):
        raise ValueError("faults must be a dictionary")
    if isinstance(total_steps, bool) or not isinstance(total_steps, int) or not 0 <= total_steps <= MAX_TOTAL_STEPS:
        raise ValueError(f"total_steps must be an integer between 0 and {MAX_TOTAL_STEPS}")
    if isinstance(noise_sigma, bool) or not isinstance(noise_sigma, (int, float)):
        raise ValueError("noise_sigma must be a number")
    if not math.isfinite(noise_sigma) or not 0 <= noise_sigma <= MAX_NOISE_SIGMA:
        raise ValueError(f"noise_sigma must be between 0 and {MAX_NOISE_SIGMA}")

    try:
        membrane_gate = run_brain_event(seed=seed, faults=faults)
    except Exception as exc:
        membrane_gate = {"event": False, "runner_error_type": type(exc).__name__}

    tau: float | None = None
    youden_j: float | None = None
    classifier_error_type: str | None = None
    actuator = C1Actuator()
    if probe_name == "no_command":
        action = actuator.apply(membrane_gate.get("event"), "no_command", None, total_steps)
    else:
        try:
            system = LinkedSystem(seed=42)
            tau, youden_j = system.calibrate()
            probe = _make_classifier_probe(system, probe_name, float(noise_sigma))
            action = actuator.apply_classifier(
                membrane_gate.get("event"), lambda: system.brain.decide(probe), total_steps
            )
            classifier_error_type = action.get("classifier_error_type")
        except Exception as exc:
            action = actuator.apply(membrane_gate.get("event"), "no_command", None, total_steps)
            classifier_error_type = type(exc).__name__

    return {
        "protocol": "brain-heart-propulsion-c1/1",
        "synthetic": True,
        "membrane_gate": membrane_gate,
        "propulsion_classifier": {
            "decision": action["classifier_decision"],
            "response": action["classifier_response"],
            "probe_name": probe_name,
            "noise_sigma": float(noise_sigma),
            "tau": tau,
            "youden_j": youden_j,
            "error_type": classifier_error_type,
        },
        **action,
    }


if __name__ == "__main__":
    print(json.dumps(run_c1_trial("forward"), indent=2))
