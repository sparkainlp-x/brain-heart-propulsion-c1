'use strict';

// Batch endpoint for the frozen C1 evaluation. It exposes only output-event
// booleans; planted/truth labels are not returned to the action evaluator.
const fs = require('node:fs');
const Brain = require('./brain.js');
const EPISODES_PER_RUN = 10;
const MAX_RUNS = 200;

function main() {
  const input = JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  if (!Array.isArray(input.runs) || input.runs.length < 1 || input.runs.length > MAX_RUNS) {
    throw new Error(`runs must contain 1 to ${MAX_RUNS} entries`);
  }
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
  const runs = input.runs.map((spec) => {
    if (!spec || typeof spec.runId !== 'string' || typeof spec.seed !== 'string' ||
        spec.seed.length < 1 || spec.seed.length > 40 ||
        !spec.faults || typeof spec.faults !== 'object') {
      throw new Error('each run needs a runId, a 1–40 character seed, and a faults object');
    }
    const result = Brain.runBrain(arch, {
      seed: spec.seed,
      episodes: EPISODES_PER_RUN,
      faults: spec.faults
    });
    if (result.episodes.length !== EPISODES_PER_RUN) throw new Error('unexpected episode count');
    return {
      runId: spec.runId,
      seed: result.opts.seed,
      faults: result.opts.faults,
      membraneEvents: result.episodes.map((episode) => !!episode.out)
    };
  });
  process.stdout.write(JSON.stringify({
    protocol: 'c1-e2e-membrane-events/1',
    synthetic: true,
    nodeVersion: process.version,
    episodesPerRun: EPISODES_PER_RUN,
    runs
  }) + '\n');
}

try {
  main();
} catch (err) {
  console.error(err && err.message ? err.message : String(err));
  process.exitCode = 1;
}
