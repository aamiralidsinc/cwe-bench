'use strict';
// The project's own tests for the affected area, from pristine copies shipped
// under /tests/functional/project. Each file is restored over its location in
// /app and run with the project's own runner so the product's tests exercise
// the agent's edits, not edited tests.
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const APP = process.env.APP || process.env.APP_DIR || '/app';
const PROJECT_SRC = path.join(__dirname, 'project');

const FILES = [
  'api_textformat.js',
  'api_protojson.js',
  'api_enum.js',
  'api_object.js',
  'api_util.js',
  'api_descriptor.js',
  'api_mapfield.js',
  'comp_options.js',
  'comp_options-parse.js',
  'comp_options-textformat.js',
];

function runProjectFile(file) {
  return () => {
    const src = path.join(PROJECT_SRC, file);
    if (!fs.existsSync(src)) throw new Error('pristine project test missing: ' + file);
    const dest = path.join(APP, 'tests', file);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
    const tape = path.join(APP, 'node_modules', '.bin', 'tape');
    const adapter = path.join(APP, 'lib', 'tape-adapter.js');
    const r = spawnSync(tape, ['-r', adapter, dest], {
      cwd: APP,
      encoding: 'utf8',
      timeout: 120000,
      env: { ...process.env, NODE_PATH: path.join(APP, 'node_modules') },
    });
    const out = (r.stdout || '') + (r.stderr || '');
    const failLine = /^# fail\s+(\d+)/m.exec(out);
    const failed = failLine ? Number(failLine[1]) : (r.status === 0 ? 0 : 1);
    if (failed > 0 || r.status !== 0) {
      throw new Error(
        'project test ' + file + ' failed (' + failed + ' failing assertions)\n' +
        out.split('\n').filter((l) => /^(not ok|#|TAP|.*Error)/.test(l)).slice(0, 40).join('\n'),
      );
    }
  };
}

module.exports = FILES.map((file) => ({
  name: 'project tests: ' + file,
  run: runProjectFile(file),
}));
