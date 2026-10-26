'use strict';

/*
 * Runs the project's own test files for the affected area against the submitted sources with the
 * project's native runner (uvu + ts-node, transpile-only). The test files are pristine copies of
 * the pinned tree, staged under the project's test directory at grading time; the library sources
 * come from the submission.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const PROJECT_ROOT = process.env.PRODUCT_ROOT || '/workspace';
const TEST_DIR = path.join(PROJECT_ROOT, 'test');
const PATTERN = '(previous-map|map|no-work-result|lazy-result|input)\\.test\\.ts$';

function uvuBin() {
  if (process.env.UVU_BIN && fs.existsSync(process.env.UVU_BIN)) return process.env.UVU_BIN;
  for (const dir of String(process.env.NODE_PATH || '').split(path.delimiter)) {
    if (!dir) continue;
    const candidate = path.join(dir, 'uvu', 'bin.js');
    if (fs.existsSync(candidate)) return candidate;
  }
  return path.join('/opt/verifier', 'node_modules', 'uvu', 'bin.js');
}

module.exports = function () {
  return [{
    classname: 'functional/F-project-suite',
    name: "F-project-suite: the project's own affected-area suites pass",
    run() {
      const bin = uvuBin();
      if (!fs.existsSync(bin)) {
        throw new Error(`the project runner is missing at ${bin}`);
      }
      const env = Object.assign({}, process.env, {
        TS_NODE_SKIP_PROJECT: 'true',
        TS_NODE_COMPILER_OPTIONS: JSON.stringify({
          module: 'commonjs',
          moduleResolution: 'node',
          target: 'es2018'
        })
      });
      const run = spawnSync(
        process.execPath,
        [bin, '-r', 'ts-node/register/transpile-only', TEST_DIR, PATTERN],
        {
          cwd: PROJECT_ROOT,
          encoding: 'utf8',
          env,
          maxBuffer: 16 * 1024 * 1024,
          timeout: 300000
        }
      );
      if (run.error) {
        throw new Error(`the project runner could not start: ${run.error.message}`);
      }
      if (run.status !== 0) {
        const output = `${run.stdout || ''}\n${run.stderr || ''}`.trim();
        const tail = output.split('\n').slice(-12).join('\n');
        throw new Error(`the project's own suites failed:\n${tail}`);
      }
    }
  }];
};
