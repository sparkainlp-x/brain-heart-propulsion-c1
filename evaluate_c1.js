'use strict';

// Exploratory, fully synthetic evaluation of the membrane event stage in C1.
// Ground-truth labels are used here only to score this model, never as its gate.
const Brain = require('./brain.js');
const Stats = require('./stats.js');

const REPLICATES = 5;
const EPISODES_PER_REPLICATE = 100;
const scenarios = [
  { id: 'clean', faults: { mode: 'collude' } },
  { id: 'within-tolerance-colluding', faults: { sensory: 1, columns: 1, mode: 'collude' } },
  { id: 'over-tolerance-sensory-colluding', faults: { sensory: 2, mode: 'collude' } }
];
const arch = Brain.planArchitecture({
  sensoryFaults: 1,
  columnFaults: 1,
  integratorFaults: 0,
  stabilizer: false,
  memory: false,
  fuse: true,
  delays: { sg: 0, gi: 0, io: 0 },
  jitter: 0,
  c: 0
});

function evaluateScenario(scenario) {
  const counts = { episodes: 0, planted: 0, noise: 0, trueOutputs: 0, falseOnPlanted: 0, falseOnNoise: 0 };
  const perSeed = [];
  for (let r = 0; r < REPLICATES; r++) {
    const seed = `c1-eval-${r + 1}`;
    const run = Brain.runBrain(arch, {
      seed,
      episodes: EPISODES_PER_REPLICATE,
      faults: scenario.faults
    });
    const local = { seed, episodes: 0, planted: 0, noise: 0, trueOutputs: 0, falseOnPlanted: 0, falseOnNoise: 0 };
    for (const ep of run.episodes) {
      counts.episodes++;
      local.episodes++;
      if (ep.planted) {
        counts.planted++;
        local.planted++;
        if (ep.out && ep.outTrue) { counts.trueOutputs++; local.trueOutputs++; }
        else if (ep.out) { counts.falseOnPlanted++; local.falseOnPlanted++; }
      } else {
        counts.noise++;
        local.noise++;
        if (ep.out) { counts.falseOnNoise++; local.falseOnNoise++; }
      }
    }
    perSeed.push(local);
  }
  const eventActivations = counts.trueOutputs + counts.falseOnPlanted + counts.falseOnNoise;
  return {
    id: scenario.id,
    faults: scenario.faults,
    counts,
    rates: {
      trueEventRecallOnPlanted: Stats.wilson(counts.trueOutputs, counts.planted),
      falseOutputOnPlanted: Stats.wilson(counts.falseOnPlanted, counts.planted),
      falseActivationOnNoise: Stats.wilson(counts.falseOnNoise, counts.noise),
      allOutputActivations: Stats.wilson(eventActivations, counts.episodes)
    },
    membraneEventGate: {
      totalEpisodes: counts.episodes,
      eventActivations,
      noEventEpisodes: counts.episodes - eventActivations,
      note: 'This is the first-stage event rate only; C1 motion also requires separate classifier acceptance.'
    },
    perSeed
  };
}

const report = {
  protocol: 'brain-heart-propulsion-c1-membrane-evaluation/1',
  synthetic: true,
  purpose: 'Measure the copied membrane-brain event stage; propulsion direction is classified separately by the Python toy.',
  design: {
    brainVersion: Brain.VERSION,
    architecture: arch.spec,
    replicates: REPLICATES,
    episodesPerReplicate: EPISODES_PER_REPLICATE,
    totalEpisodesPerScenario: REPLICATES * EPISODES_PER_REPLICATE,
    interval: '95% Wilson score interval',
    groundTruthUsedFor: 'scoring only; never used as the membrane gate',
    composition: 'C1 requires this event plus independent acceptance by the propulsion package classifier.',
    limitations: [
      'Generated toy vectors only; not biological or hardware data.',
      'The batch rates describe only the membrane event stage, not end-to-end C1 motion.',
      'Episodes are outputs of a deterministic software model; intervals are descriptive model-frequency intervals.',
      'The fault scenarios are chosen simulations, not estimates of real fault rates.',
      'An output event is only an imposed permission bit; it does not encode direction.'
    ]
  },
  scenarios: scenarios.map(evaluateScenario)
};
process.stdout.write(JSON.stringify(report, null, 2) + '\n');
