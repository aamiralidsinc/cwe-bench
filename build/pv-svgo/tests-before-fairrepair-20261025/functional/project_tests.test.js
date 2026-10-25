'use strict';

const { spawnSync } = require('child_process');
const path = require('path');

const JEST = path.join('/workspace', 'node_modules', 'jest', 'bin', 'jest.js');

function runJest(args, label) {
  const result = spawnSync(process.execPath, [JEST, ...args], {
    cwd: '/workspace',
    env: { ...process.env, NODE_OPTIONS: '--experimental-vm-modules', CI: '1' },
    encoding: 'utf8',
    timeout: 300000,
  });
  if (result.error) {
    throw new Error(`${label}: could not start the project test runner: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const output = `${result.stdout || ''}\n${result.stderr || ''}`.trim();
    throw new Error(`${label} failed (exit ${result.status}):\n${output.slice(-4000)}`);
  }
}

module.exports = {
  tests: [
    {
      name: 'project_plugin_fixtures_still_pass',
      fn() {
        runJest(['test/plugins/_index.test.js'], 'project plugin fixtures');
      },
    },
    {
      name: 'project_library_tests_still_pass',
      fn() {
        runJest(['lib/svgo.test.js', 'lib/svgo-node.test.js'], 'project library tests');
      },
    },
  ],
};
