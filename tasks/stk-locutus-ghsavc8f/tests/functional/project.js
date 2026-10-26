'use strict';

/*
 * The project's own generated vitest suite for the affected functions. The suite is run in one
 * child process against the submitted workspace; each file becomes one functional case, so a
 * regression is attributed to the file that carries it. The test sources are restored from the
 * hidden copy at grade time, never read from the submission.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const FILES = [
  'test/generated/php/strings/parse_str.vitest.ts',
  'test/generated/php/var/unserialize.vitest.ts',
  'test/generated/php/info/ini_set.vitest.ts',
  'test/generated/php/array/array_merge.vitest.ts',
  'test/generated/php/array/array_merge_recursive.vitest.ts',
  'test/generated/php/array/array_replace.vitest.ts',
  'test/generated/php/array/array_replace_recursive.vitest.ts',
  'test/generated/php/array/array_change_key_case.vitest.ts',
  'test/generated/php/array/array_combine.vitest.ts',
];

module.exports = function () {
  const root = process.env.PRODUCT_ROOT || '/workspace';
  const deps = process.env.VERIFIER_DEPS || '/opt/verifier-locutus';
  const vitest = path.join(deps, 'node_modules', 'vitest', 'vitest.mjs');
  const out = path.join('/tmp', `locutus-project-${process.pid}.json`);
  try { fs.rmSync(out, { force: true }); } catch (_) { /* ignore */ }

  const entries = [];
  if (!fs.existsSync(vitest)) {
    entries.push({
      classname: 'functional/project', name: 'project tests: runner available',
      precomputed: { ok: false, message: `the warmed vitest tree is missing at ${vitest}` },
    });
    return entries;
  }

  const result = spawnSync(process.execPath,
    [vitest, 'run', '--reporter=json', '--outputFile=' + out, '--no-color'].concat(FILES),
    { cwd: root, encoding: 'utf8', timeout: 300000, env: process.env });

  let data = null;
  try {
    data = JSON.parse(fs.readFileSync(out, 'utf8'));
  } catch (_) { data = null; }

  if (!data || !Array.isArray(data.testResults)) {
    const tail = String((result && (result.stderr || result.stdout)) || '').trim().slice(-800);
    entries.push({
      classname: 'functional/project', name: 'project tests: suite runs',
      precomputed: { ok: false, message: `the project suite did not produce a result file: ${tail}` },
    });
    return entries;
  }

  const byName = new Map();
  for (const r of data.testResults) byName.set(String(r.name), r);

  for (const rel of FILES) {
    let found = null;
    for (const [name, r] of byName) {
      if (name === rel || name.endsWith('/' + rel)) { found = r; break; }
    }
    if (!found) {
      entries.push({
        classname: 'functional/project', name: `project: ${rel}`,
        precomputed: { ok: false, message: `no result for ${rel}` },
      });
      continue;
    }
    const assertions = Array.isArray(found.assertionResults) ? found.assertionResults : [];
    const failed = assertions.filter(a => a.status !== 'passed');
    const ok = found.status === 'passed' && assertions.length > 0 && failed.length === 0;
    let message = '';
    if (!ok) {
      if (!assertions.length) message = String(found.message || 'the suite reported no tests');
      else message = failed.map(a => `${a.fullName || a.title}: ${(a.failureMessages || []).join(' ').slice(0, 300)}`).join(' | ');
    }
    entries.push({
      classname: 'functional/project', name: `project: ${rel}`,
      precomputed: { ok, message: message.slice(0, 1500) },
    });
  }

  return entries;
};
