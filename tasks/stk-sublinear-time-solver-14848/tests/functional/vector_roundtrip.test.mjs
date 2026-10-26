import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { connectSolver, findFile } from '../support/mcp.mjs';

const IDENTITY_2 = {
  values: [1, 1], rowIndices: [0, 1], colIndices: [0, 1], rows: 2, cols: 2,
};

async function withServer(fn) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-vector-fn-'));
  const home = path.join(base, 'home');
  const cwd = path.join(base, 'run');
  const vectorDir = path.join(base, 'vectors');
  fs.mkdirSync(home, { recursive: true });
  fs.mkdirSync(cwd, { recursive: true });
  const client = await connectSolver({ home, cwd, vectorDir });
  try {
    await fn({ client, base, home, cwd, vectorDir });
  } finally {
    await client.close().catch(() => {});
    fs.rmSync(base, { recursive: true, force: true, maxRetries: 3 });
  }
}

test('vector function: saving and then solving with the saved name works', async () => {
  await withServer(async ({ client, base }) => {
    const saved = await client.callTool({
      name: 'saveVectorToFile', arguments: { vector: [3.5, 5.25], file_path: 'roundtrip.json' },
    });
    assert.equal(saved && saved.isError ? true : false, false, 'the save failed');
    assert.ok(findFile(base, 'roundtrip.json'), 'the save produced no file for the supplied name');

    const solved = await client.callTool({
      name: 'solveTrueSublinear', arguments: { matrix: IDENTITY_2, vector_file: 'roundtrip.json' },
    });
    assert.equal(solved && solved.isError ? true : false, false, 'the solve failed');
    const text = JSON.stringify(solved);
    assert.match(text, /3\.5/, 'the solved vector does not match the saved data');
    assert.match(text, /5\.25/, 'the solved vector does not match the saved data');
  });
});

test('vector function: the format follows the file extension', async () => {
  await withServer(async ({ client, base }) => {
    const saved = await client.callTool({
      name: 'saveVectorToFile', arguments: { vector: [1, 2, 3], file_path: 'roundtrip.csv' },
    });
    assert.equal(saved && saved.isError ? true : false, false, 'the save failed');
    const file = findFile(base, 'roundtrip.csv');
    assert.ok(file, 'the save produced no file for the supplied name');
    assert.equal(fs.readFileSync(file, 'utf8').replace(/\s+/g, ''), '1,2,3',
      'the comma-separated format was not used');
  });
});

test('vector function: a name without a known extension defaults to JSON', async () => {
  await withServer(async ({ client, base }) => {
    const saved = await client.callTool({
      name: 'saveVectorToFile', arguments: { vector: [4, 5], file_path: 'plainvector' },
    });
    assert.equal(saved && saved.isError ? true : false, false, 'the save failed');
    const file = findFile(base, 'plainvector');
    assert.ok(file, 'the save produced no file for the supplied name');
    assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), [4, 5],
      'the default format was not JSON');
  });
});
