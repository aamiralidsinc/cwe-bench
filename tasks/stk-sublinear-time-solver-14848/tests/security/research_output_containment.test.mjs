import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { ROOT } from '../support/env.mjs';

const RESULTS = { answer: 'sample', citations: [], metadata: {} };

async function withProject(fn) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-output-'));
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

function savedAnywhere(dir) {
  if (!fs.existsSync(dir)) return false;
  return fs.readdirSync(dir).length > 0;
}

test('output: an absolute output location is refused and nothing is written', async () => {
  await withProject(async ({ base, manager }) => {
    const outside = path.join(base, 'absolute-output');
    await assert.rejects(
      async () => manager.saveToFile(RESULTS, 'q', 'json', { outputPath: outside, useQuerySubfolder: false }),
      'the absolute output location was accepted');
    assert.equal(savedAnywhere(outside), false, 'the refused output created files outside');
  });
});

test('output: an output location that climbs out of the project is refused', async () => {
  await withProject(async ({ base, manager }) => {
    const outside = path.join(base, 'climbed-output');
    await assert.rejects(
      async () => manager.saveToFile(RESULTS, 'q', 'json', { outputPath: '../climbed-output', useQuerySubfolder: false }),
      'the climbing output location was accepted');
    assert.equal(savedAnywhere(outside), false, 'the refused output created files outside');
  });
});

test('output: a linked directory inside the project is not followed', async () => {
  await withProject(async ({ base, project, manager }) => {
    const target = path.join(base, 'linked-output');
    fs.mkdirSync(target, { recursive: true });
    fs.symlinkSync(target, path.join(project, 'reports'), 'dir');
    await assert.rejects(
      async () => manager.saveToFile(RESULTS, 'q', 'json', { outputPath: 'reports', useQuerySubfolder: false }),
      'the linked output directory was accepted');
    assert.equal(savedAnywhere(target), false, 'the output was written through a link outside');
  });
});

test('output: a link below a relative output location is not followed', async () => {
  await withProject(async ({ base, project, manager }) => {
    const target = path.join(base, 'nested-linked-output');
    fs.mkdirSync(target, { recursive: true });
    fs.symlinkSync(target, path.join(project, 'nested'), 'dir');
    await assert.rejects(
      async () => manager.saveToFile(RESULTS, 'q', 'json', { outputPath: 'nested/deeper', useQuerySubfolder: false }),
      'the nested linked output location was accepted');
    assert.equal(savedAnywhere(target), false, 'the output was written through a nested link outside');
  });
});
