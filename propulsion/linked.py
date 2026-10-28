"""brain-heart-propulsion v0.1.0 — brain decides, heart paces,
propulsion moves, sensor reports.

Stdlib-only Python, seeded, reproducible, AGPL-3.0-only.

Lineage, reused exactly
-----------------------
- membrane-brain / membrane-heart: seeded neurons, k-NN edges,
  Dijkstra delays, ENVELOPED phasor waves (amplitude decays
  with distance, phase advances with distance). Pure-phase
  waves were falsified in membrane-heart and are not repeated.
- refusing-membrane / membrane-vs-hopfield: REJECT iff max
  |overlap| < tau, tau calibrated once via Youden's J and
  frozen, midpoint-of-max-J.
- membrane-propulsion v0.2.0: 64-oscillator ring, probe
  velocity = local phase gradient (assumed law, not a
  physical force), passive sensor reading k_est, omega and
  coherence from gradients alone.

The link (design choices, see PREREG.md)
----------------------------------------
1. BRAIN: a probe field (128-dim) is projected on 4 stored
   enveloped waves. Winner names a response; the frozen gate
   refuses it if max |overlap| < tau.
2. MAPPING (imposed): forward -> k = +1, reverse -> k = -1,
   hold -> k = 0, rest -> k = 0 (fail-safe default).
3. HEART: a clock, not a heartbeat. Propulsion moves only on
   heart ticks, one tick every HEART_PERIOD_STEPS = 10 steps.
   The period is chosen, not measured.
4. PROPULSION: on a tick, the probe moves by the ring's local
   phase gradient at its site. For a locked twist k, that
   gradient is 2*pi*k/64, so 200 ticks give about 19.6 sites
   (by construction, as in membrane-propulsion's +20).
5. SENSOR: after the run, k_est = round(gradient * 64 / 2*pi),
   omega = -1.000 in the drive frame (by construction),
   coherence = 1 - spread of local gradients (1.0 for a
   perfect twist, lower if the ring is untwisted/noisy).
   The sensor is never told the intended drive.

What this is NOT
----------------
Not a brain, not a heart, not a nervous system, not a
propulsion device, not neuroscience, not a medical device,
not a diagnosis, not a measurement of any real person.
Delays are distance units, not milliseconds. Frequencies in
this package are in arbitrary toy units, except where a
module explicitly reuses an illustrative Hz band.
"""

import heapq
import math
import random

__version__ = "0.1.0"

HEART_PERIOD_STEPS = 10
RING_N = 64
BRAIN_N = 128


# ---------------------------------------------------------------- helpers
def normalize(v):
    n = math.sqrt(sum(abs(c) ** 2 for c in v))
    if n == 0:
        raise ValueError("cannot normalize a zero vector")
    return [c / n for c in v]


def overlap(field, pattern):
    return sum(p.conjugate() * f for p, f in zip(pattern, field))


def noisy(field, sigma, rng):
    return normalize(
        [c + complex(rng.gauss(0, sigma), rng.gauss(0, sigma))
         for c in field]
    )


def rand_field(n, rng):
    return normalize(
        [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
    )


def wrap_pi(a):
    while a > math.pi:
        a -= 2.0 * math.pi
    while a <= -math.pi:
        a += 2.0 * math.pi
    return a


# ---------------------------------------------------------------- brain graph
class BrainGraph:
    """128 seeded nodes, k-NN edges, Dijkstra delays, enveloped waves."""

    def __init__(self, seed=42, k=4, width=12.0, period=40.0):
        self.seed = seed
        rng = random.Random(seed)
        pts = []
        while len(pts) < BRAIN_N:
            x = rng.uniform(-24.0, 24.0)
            y = rng.uniform(-28.0, 28.0)
            if (x / 24.0) ** 2 + (y / 28.0) ** 2 <= 1.0:
                pts.append((x, y))
        self.pts = pts
        self.edges = set()
        for a in range(BRAIN_N):
            dists = sorted(
                ((pts[a][0] - pts[b][0]) ** 2
                 + (pts[a][1] - pts[b][1]) ** 2, b)
                for b in range(BRAIN_N) if b != a
            )
            for _, b in dists[:k]:
                self.edges.add((min(a, b), max(a, b)))
        self.edges = sorted(self.edges)
        self.width = width
        self.period = period

    def neighbours(self, nid):
        out = []
        for a, b in self.edges:
            if a == nid:
                out.append(b)
            elif b == nid:
                out.append(a)
        return sorted(out)

    def delays_from(self, source):
        times = {i: math.inf for i in range(BRAIN_N)}
        times[source] = 0.0
        heap = [(0.0, source)]
        while heap:
            t, nid = heapq.heappop(heap)
            if t > times[nid]:
                continue
            for mid in self.neighbours(nid):
                w = math.hypot(self.pts[nid][0] - self.pts[mid][0],
                               self.pts[nid][1] - self.pts[mid][1])
                if t + w < times[mid]:
                    times[mid] = t + w
                    heapq.heappush(heap, (times[mid], mid))
        return [times[i] for i in range(BRAIN_N)]

    def wave(self, source):
        delays = self.delays_from(source)
        out = []
        for d in delays:
            if math.isinf(d):
                out.append(0j)
                continue
            amp = math.exp(-(d * d) / (2.0 * self.width * self.width))
            phase = 2.0 * math.pi * d / self.period
            out.append(amp * complex(math.cos(phase), math.sin(phase)))
        return normalize(out)


class Brain:
    RESPONSE_NAMES = ("forward", "reverse", "hold", "rest")
    # Mapping is imposed, see PREREG.md.
    RESPONSE_TO_DRIVE = {"forward": 1, "reverse": -1,
                         "hold": 0, "rest": 0}

    def __init__(self, seed=42):
        self.graph = BrainGraph(seed=seed)
        # Four distinct seeds spread across the node list.
        self.seed_ids = [0, 32, 64, 96]
        self.patterns = [self.graph.wave(s) for s in self.seed_ids]
        self.tau = None

    def overlaps(self, field):
        return [overlap(field, p) for p in self.patterns]

    def max_overlap(self, field):
        return max(abs(m) for m in self.overlaps(field))

    def calibrate(self, in_probes, ood_probes, grid=101):
        in_max = [self.max_overlap(f) for f in in_probes]
        ood_max = [self.max_overlap(f) for f in ood_probes]
        best_j, best_taus = -2.0, []
        for step in range(grid + 1):
            tau = step / grid
            tpr = sum(1 for v in in_max if v >= tau) / len(in_max)
            fpr = sum(1 for v in ood_max if v >= tau) / len(ood_max)
            j = tpr - fpr
            if j > best_j + 1e-12:
                best_j, best_taus = j, [tau]
            elif abs(j - best_j) <= 1e-12:
                best_taus.append(tau)
        self.tau = (best_taus[0] + best_taus[-1]) / 2.0
        return self.tau, best_j

    def decide(self, field):
        ms = self.overlaps(field)
        winner = max(range(len(ms)), key=lambda i: abs(ms[i]))
        if self.tau is not None and self.max_overlap(field) < self.tau:
            return "reject", None, winner
        return "accept", self.RESPONSE_NAMES[winner], winner


# ---------------------------------------------------------------- heart clock
class HeartClock:
    """A clock, not a heartbeat. Ticks every HEART_PERIOD_STEPS.

    The period is a chosen design parameter. Nothing here is
    a measured heart rate, ECG, or cardiac model.
    """

    def __init__(self, period_steps=HEART_PERIOD_STEPS):
        self.period = period_steps
        self.step_count = 0
        self.ticks = 0

    def step(self):
        """Advance one step. Returns True iff this step is a tick."""
        self.step_count += 1
        if self.step_count % self.period == 0:
            self.ticks += 1
            return True
        return False


# ---------------------------------------------------------------- propulsion ring
class PropulsionRing:
    """64-site ring, twisted phase state, probe, passive sensor."""

    def __init__(self, n=RING_N):
        self.n = n
        self.drive = 0
        self.position = 0.0
        self.phases = [0.0] * n

    def set_drive(self, k):
        self.drive = k
        self.phases = [2.0 * math.pi * k * i / self.n
                       for i in range(self.n)]

    def gradient_at(self, pos):
        i = int(math.floor(pos)) % self.n
        nxt = (i + 1) % self.n
        return wrap_pi(self.phases[nxt] - self.phases[i])

    def tick_move(self):
        """Move the probe by the local gradient. Returns displacement."""
        g = self.gradient_at(self.position)
        self.position += g
        return g

    def sensor(self):
        """Passive read: k_est, omega, coherence, from gradients only."""
        grads = []
        for i in range(self.n):
            nxt = (i + 1) % self.n
            grads.append(wrap_pi(self.phases[nxt] - self.phases[i]))
        mean_g = sum(grads) / len(grads)
        k_est = int(round(mean_g * self.n / (2.0 * math.pi)))
        spread = (sum(abs(wrap_pi(g - mean_g)) for g in grads)
                  / len(grads) / math.pi)
        coherence = max(0.0, 1.0 - spread)
        return {"k_est": k_est, "omega": -1.000,
                "coherence": coherence, "mean_gradient": mean_g}


# ---------------------------------------------------------------- linked system
class LinkedResult:
    def __init__(self, decision, response, drive, displacement,
                 heart_ticks, sensor):
        self.decision = decision
        self.response = response
        self.drive = drive
        self.displacement = displacement
        self.heart_ticks = heart_ticks
        self.sensor = sensor

    def __repr__(self):
        return (f"LinkedResult({self.decision!r}, {self.response!r}, "
                f"drive={self.drive}, disp={self.displacement:.2f}, "
                f"ticks={self.heart_ticks}, sensor={self.sensor})")


class LinkedSystem:
    """Brain -> heart clock -> propulsion ring -> sensor."""

    def __init__(self, seed=42):
        self.brain = Brain(seed=seed)
        self.heart = HeartClock()
        self.ring = PropulsionRing()

    def calibrate(self):
        rng = random.Random(11)
        in_p = [noisy(self.brain.patterns[k % 4], 0.15, rng)
                for k in range(100)]
        ood_p = [rand_field(BRAIN_N, rng) for _ in range(100)]
        return self.brain.calibrate(in_p, ood_p)

    def run(self, probe, total_steps=2000):
        if self.brain.tau is None:
            raise ValueError("calibrate the brain gate first")
        decision, response, _ = self.brain.decide(probe)
        if decision == "reject":
            drive = 0
        else:
            drive = Brain.RESPONSE_TO_DRIVE[response]
        self.ring.set_drive(drive)
        start = self.ring.position
        # Fresh clock per run, so ticks are counted for this run only.
        self.heart = HeartClock()
        for _ in range(total_steps):
            if self.heart.step():
                self.ring.tick_move()
        displacement = self.ring.position - start
        return LinkedResult(decision, response, drive, displacement,
                            self.heart.ticks, self.ring.sensor())
