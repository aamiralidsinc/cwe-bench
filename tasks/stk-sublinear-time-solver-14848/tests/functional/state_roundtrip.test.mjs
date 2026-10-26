import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { connectConsciousness, findFile } from '../support/mcp.mjs';

async function withServer(fn) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cwe-state-fn-'));
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

test('state function: saving and then loading by name works', async () => {
  await withServer(async ({ client, base }) => {
    const saved = await client.callTool({ name: 'export_state', arguments: { filepath: 'snapshot.json' } });
    assert.equal(saved && saved.isError ? true : false, false, 'the save failed');
    assert.ok(findFile(base, 'snapshot.json'), 'the save produced no file for the supplied name');

    const loaded = await client.callTool({ name: 'import_state', arguments: { filepath: 'snapshot.json' } });
    assert.equal(loaded && loaded.isError ? true : false, false, 'the load failed');
    assert.match(JSON.stringify(loaded), /success/);
  });
});

test('state function: loading by name reads the stored snapshot', async () => {
  await withServer(async ({ client, base }) => {
    const saved = await client.callTool({ name: 'export_state', arguments: { filepath: 'memory.json' } });
    assert.equal(saved && saved.isError ? true : false, false, 'the save failed');
    const file = findFile(base, 'memory.json');
    assert.ok(file, 'the save produced no file for the supplied name');

    const snapshot = JSON.parse(fs.readFileSync(file, 'utf8'));
    snapshot.consciousness = snapshot.consciousness || {};
    snapshot.consciousness.selfAwareness = 0.6123;
    fs.writeFileSync(file, JSON.stringify(snapshot));

    const loaded = await client.callTool({ name: 'import_state', arguments: { filepath: 'memory.json' } });
    assert.equal(loaded && loaded.isError ? true : false, false, 'the load failed');
    assert.match(JSON.stringify(loaded), /0\.6123/,
      'the loaded state does not reflect the stored snapshot');
  });
});

test('state function: a name with dots is accepted', async () => {
  await withServer(async ({ client, base }) => {
    const saved = await client.callTool({ name: 'export_state', arguments: { filepath: 'snapshot.v2.json' } });
    assert.equal(saved && saved.isError ? true : false, false, 'a dotted name was rejected');
    assert.ok(findFile(base, 'snapshot.v2.json'), 'the save produced no file for the dotted name');
    const loaded = await client.callTool({ name: 'import_state', arguments: { filepath: 'snapshot.v2.json' } });
    assert.equal(loaded && loaded.isError ? true : false, false, 'loading the dotted name failed');
  });
});
