"""Demo for brain-heart-propulsion v0.1.0. Run: python demo.py"""
import random

from linked import BRAIN_N, LinkedSystem, noisy, rand_field


def main():
    sys = LinkedSystem(seed=42)
    tau, j = sys.calibrate()
    print("brain-heart-propulsion v0.1.0")
    print(f"brain gate: tau = {tau:.3f}, Youden J = {j:.3f} (frozen)")
    print(f"brain patterns: {len(sys.brain.patterns)}, "
          f"ring sites: {sys.ring.n}, heart period: 10 steps/tick")
    for name, probe in [
        ("forward", sys.brain.patterns[0]),
        ("reverse", sys.brain.patterns[1]),
        ("hold", sys.brain.patterns[2]),
        ("rest", sys.brain.patterns[3]),
    ]:
        res = sys.run(probe)
        print(f"{name}: {res.decision} {res.response} drive {res.drive} "
              f"disp {res.displacement:.2f} ticks {res.heart_ticks} "
              f"sensor k_est {res.sensor['k_est']} "
              f"omega {res.sensor['omega']:.3f} "
              f"coherence {res.sensor['coherence']:.3f}")
    rng = random.Random(7)
    res = sys.run(rand_field(BRAIN_N, rng))
    print(f"random: {res.decision} drive {res.drive} "
          f"disp {res.displacement:.2f} sensor k_est {res.sensor['k_est']}")
    rng2 = random.Random(99)
    ok = 0
    for _ in range(40):
        probe = noisy(sys.brain.patterns[0], 0.15, rng2)
        res = sys.run(probe)
        if res.decision == "accept" and res.response == "forward":
            ok += 1
    print(f"fresh noisy forward (sigma 0.15): {ok}/40 correct")
    print(f"tau after runs: {sys.brain.tau:.3f} (unchanged)")


if __name__ == "__main__":
    main()
