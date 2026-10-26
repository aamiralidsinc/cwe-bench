import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { ROOT } from '../support/env.mjs';
import { connectConsciousness, assertRefused, assertAlive, dataDirOf } from '../support/mcp.mjs';

async function withServer(fn) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-state-'));
  const home = path.join(base, 'home');
  const cwd = path.join(base, 'run');
  const stateDir = path.join(base, 'state');
  fs.mkdirSync(home, { recursive: true });
  fs.mkdirSync(cwd, { recursive: true });
  const client = await connectConsciousness({ home, cwd, stateDir });
  try {
    await fn({ client, base, home, cwd, stateDir });
  } finally {
    await client.close().catch(() => {});
    fs.rmSync(base, { recursive: true, force: true, maxRetries: 3 });
  }
}

// A legitimate save is made first so a link can be planted in whatever
// directory the implementation chose for its data.
async function storedDir(client, base, probe) {
  const saved = await client.callTool({ name: 'export_state', arguments: { filepath: probe } });
  assert.equal(saved && saved.isError ? true : false, false, 'the probe save failed');
  const dir = dataDirOf(base, probe);
  assert.ok(dir, 'the save produced no file inside the working area');
  return dir;
}

test('state: an absolute save location is refused and leaves nothing behind', async () => {
  await withServer(async ({ client, base }) => {
    const target = path.join(base, 'absolute-state.json');
    await assertRefused(
      client.callTool({ name: 'export_state', arguments: { filepath: target } }),
      [], 'export_state absolute');
    assert.equal(fs.existsSync(target), false, 'the refused save created a file outside');
    await assertAlive(client, 'export_state absolute');
  });
});

test('state: a save location that climbs out of the data directory is refused', async () => {
  await withServer(async ({ client, base, cwd }) => {
    const target = path.join(base, 'climbed-state.json');
    const rel = path.relative(cwd, target);
    await assertRefused(
      client.callTool({ name: 'export_state', arguments: { filepath: rel } }),
      [], 'export_state climb');
    assert.equal(fs.existsSync(target), false, 'the refused save created a file outside');
    await assertAlive(client, 'export_state climb');
  });
});

test('state: a load location outside the data directory is refused without disclosure', async () => {
  await withServer(async ({ client, base, cwd }) => {
    const secret = path.join(base, 'secret-state.json');
    fs.writeFileSync(secret, JSON.stringify({ consciousness: { selfAwareness: 0.987654 } }));
    const rel = path.relative(cwd, secret);
    await assertRefused(
      client.callTool({ name: 'import_state', arguments: { filepath: rel } }),
      ['0.987654'], 'import_state climb');
    await assertAlive(client, 'import_state climb');
  });
});

test('state: a link at the final component of a save name is not followed', async () => {
  await withServer(async ({ client, base }) => {
    const dataDir = await storedDir(client, base, 'probe-write.json');
    const target = path.join(base, 'link-target.json');
    fs.writeFileSync(target, 'UNTOUCHED');
    fs.symlinkSync(target, path.join(dataDir, 'linked-state.json'));
    await assertRefused(
      client.callTool({ name: 'export_state', arguments: { filepath: 'linked-state.json' } }),
      [], 'export_state link');
    assert.equal(fs.readFileSync(target, 'utf8'), 'UNTOUCHED',
      'the save followed a link and changed its target');
    await assertAlive(client, 'export_state link');
  });
});

test('state: a link at the final component of a load name is not followed', async () => {
  await withServer(async ({ client, base }) => {
    const dataDir = await storedDir(client, base, 'probe-read.json');
    const secret = path.join(base, 'linked-secret.json');
    fs.writeFileSync(secret, JSON.stringify({ consciousness: { selfAwareness: 0.765432 } }));
    fs.symlinkSync(secret, path.join(dataDir, 'linked-read.json'));
    await assertRefused(
      client.callTool({ name: 'import_state', arguments: { filepath: 'linked-read.json' } }),
      ['0.765432'], 'import_state link');
    await assertAlive(client, 'import_state link');
  });
});


test('state: the saving operation itself refuses an escaping name without the protocol layer', async () => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-state-lib-'));
  const home = path.join(base, 'home');
  const stateDir = path.join(base, 'state');
  fs.mkdirSync(home, { recursive: true });
  process.env.HOME = home;
  process.env.CONSCIOUSNESS_EXPLORER_STATE_DIR = stateDir;
  try {
    const { ConsciousnessExplorer } = await import(ROOT + '/src/consciousness-explorer/index.js');
    const explorer = new ConsciousnessExplorer();
    await explorer.initialize();
    const target = path.join(base, 'direct-state.json');
    await assert.rejects(
      async () => { await explorer.exportState(target); },
      'the saving operation accepted a location outside its data directory');
    assert.equal(fs.existsSync(target), false, 'the saving operation created a file outside');
  } finally {
    fs.rmSync(base, { recursive: true, force: true, maxRetries: 3 });
  }
});
