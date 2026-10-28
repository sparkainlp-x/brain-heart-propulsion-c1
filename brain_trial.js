'use strict';

// Local C1 bridge endpoint: run the copied synthetic membrane-brain model.
// The output event is used as a permission bit; no ground-truth label is read.
const fs = require('node:fs');
const Brain = require('./brain.js');

function main() {
  const input = JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  if (typeof input.seed !== 'string' || input.seed.length < 1 || input.seed.length > 40) {
    throw new Error('seed must be a string of 1 to 40 characters');
  }
  const faults = input.faults && typeof input.faults === 'object' ? input.faults : {};
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
  const run = Brain.runBrain(arch, { seed: input.seed, episodes: 2, faults });
  const episode = run.episodes[0];
  if (!episode) throw new Error('brain simulation returned no episode');
  process.stdout.write(JSON.stringify({
    protocol: 'brain-heart-propulsion-c1/1',
    synthetic: true,
    brain: {
      source: 'membrane-arena/brain.js',
      version: Brain.VERSION,
      seed: run.opts.seed,
      episodeIndex: 0,
      event: !!episode.out,
      outputStep: episode.out ? episode.outStep : null,
      gatesReleased: episode.gatesReleased,
      faults: run.opts.faults
    }
  }) + '\n');
}

try {
  main();
} catch (err) {
  console.error(err && err.message ? err.message : String(err));
  process.exitCode = 1;
}
