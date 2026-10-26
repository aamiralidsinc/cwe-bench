import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { ROOT } from '../support/env.mjs';

const RESULTS = { answer: 'sample answer', citations: [], metadata: {} };

async function withProject(fn) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-output-fn-'));
  const project = path.join(base, 'project');
  fs.mkdirSync(project, { recursive: true });
  const { OutputManager } = await import(ROOT + '/npx/goalie/dist/utils/output-manager.js');
  const manager = new OutputManager();
  const previous = process.cwd();
  process.chdir(project);
  try {
    await fn({ base, project, manager });
  } finally {
    process.chdir(previous);
    fs.rmSync(base, { recursive: true, force: true, maxRetries: 3 });
  }
}

function filesUnder(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).map((name) => path.join(dir, name));
}

test('output function: the default location works', async () => {
  await withProject(async ({ project, manager }) => {
    const saved = await manager.saveToFile(RESULTS, 'query', 'json', { useQuerySubfolder: false });
    assert.ok(Array.isArray(saved) && saved.length >= 1, 'the default save returned no files');
    const dir = path.join(project, '.research');
    const files = filesUnder(dir);
    assert.ok(files.length >= 1, 'the default location holds no output');
    assert.deepEqual(JSON.parse(fs.readFileSync(files[0], 'utf8')), RESULTS);
  });
});

test('output function: a relative location inside the project works', async () => {
  await withProject(async ({ project, manager }) => {
    const saved = await manager.saveToFile(RESULTS, 'query', 'markdown', {
      outputPath: path.join('reports', 'sub'), useQuerySubfolder: false,
    });
    assert.ok(Array.isArray(saved) && saved.length >= 1, 'the relative save returned no files');
    const dir = path.join(project, 'reports', 'sub');
    const files = filesUnder(dir);
    assert.ok(files.length >= 1, 'the relative location holds no output');
    assert.match(fs.readFileSync(files[0], 'utf8'), /sample answer/);
  });
});
