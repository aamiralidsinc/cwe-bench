import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { connectSolver, assertRefused, dataDirOf } from '../support/mcp.mjs';

const IDENTITY_2 = {
  values: [1, 1], rowIndices: [0, 1], colIndices: [0, 1], rows: 2, cols: 2,
};

async function withServer(fn) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-vector-'));
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

async function storedDir(client, base, probe) {
  const saved = await client.callTool({
    name: 'saveVectorToFile', arguments: { vector: [1], file_path: probe },
  });
  assert.equal(saved && saved.isError ? true : false, false, 'the probe save failed');
  const dir = dataDirOf(base, probe);
  assert.ok(dir, 'the save produced no file inside the working area');
  return dir;
}

test('vector: an absolute save location is refused and leaves nothing behind', async () => {
  await withServer(async ({ client, base }) => {
    const target = path.join(base, 'absolute-vector.json');
    await assertRefused(
      client.callTool({ name: 'saveVectorToFile', arguments: { vector: [1, 2, 3], file_path: target } }),
      [], 'saveVectorToFile absolute');
    assert.equal(fs.existsSync(target), false, 'the refused save created a file outside');
  });
});

test('vector: a save location that climbs out of the data directory is refused', async () => {
  await withServer(async ({ client, base, cwd }) => {
    const target = path.join(base, 'climbed-vector.json');
    const rel = path.relative(cwd, target);
    await assertRefused(
      client.callTool({ name: 'saveVectorToFile', arguments: { vector: [1, 2], file_path: rel } }),
      [], 'saveVectorToFile climb');
    assert.equal(fs.existsSync(target), false, 'the refused save created a file outside');
  });
});

test('vector: a refused save creates no directory outside the data directory', async () => {
  await withServer(async ({ client, base }) => {
    const target = path.join(base, 'made', 'deep', 'nested-vector.json');
    await assertRefused(
      client.callTool({ name: 'saveVectorToFile', arguments: { vector: [1, 2], file_path: target } }),
      [], 'saveVectorToFile nested');
    assert.equal(fs.existsSync(path.join(base, 'made')), false,
      'the refused save created a directory outside');
  });
});

test('vector: a load location outside the data directory is refused without disclosure', async () => {
  await withServer(async ({ client, base }) => {
    const secret = path.join(base, 'secret-vector.json');
    fs.writeFileSync(secret, JSON.stringify([7.25, 4.75]));
    await assertRefused(
      client.callTool({ name: 'solveTrueSublinear', arguments: { matrix: IDENTITY_2, vector_file: secret } }),
      ['7.25'], 'solveTrueSublinear absolute');
  });
});

test('vector: a link at the final component of a save name is not followed', async () => {
  await withServer(async ({ client, base }) => {
    const dataDir = await storedDir(client, base, 'probe-save.json');
    const target = path.join(base, 'link-vector-target.json');
    fs.writeFileSync(target, 'UNTOUCHED');
    fs.symlinkSync(target, path.join(dataDir, 'linked-vector.json'));
    await assertRefused(
      client.callTool({ name: 'saveVectorToFile', arguments: { vector: [9, 9], file_path: 'linked-vector.json' } }),
      [], 'saveVectorToFile link');
    assert.equal(fs.readFileSync(target, 'utf8'), 'UNTOUCHED',
      'the save followed a link and changed its target');
  });
});

test('vector: a link at the final component of a load name is not followed', async () => {
  await withServer(async ({ client, base }) => {
    const dataDir = await storedDir(client, base, 'probe-load.json');
    const secret = path.join(base, 'linked-vector-secret.json');
    fs.writeFileSync(secret, JSON.stringify([7.25, 4.75]));
    fs.symlinkSync(secret, path.join(dataDir, 'linked-load.json'));
    await assertRefused(
      client.callTool({ name: 'solveTrueSublinear', arguments: { matrix: IDENTITY_2, vector_file: 'linked-load.json' } }),
      ['7.25'], 'solveTrueSublinear link');
  });
});

