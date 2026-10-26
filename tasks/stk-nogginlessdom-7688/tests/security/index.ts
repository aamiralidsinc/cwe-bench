// Security cases for the snapshot writers. Every case drives a product entry
// point, expects a refusal (a thrown error) and checks the filesystem effect
// itself. Nothing here assumes a particular error message or status.
import * as crypto from 'node:crypto';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import {
  expect,
  setUpdateMode,
  SnapshotClient,
  NodeSnapshotEnvironment,
  SnapshotManager,
} from '../support/product.ts';
import type { Case } from '../support/runner.ts';

function outside(prefix: string): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function projectDir(prefix: string): string {
  return fs.mkdtempSync(path.join(process.cwd(), prefix));
}

function mustThrow(action: () => void): void {
  let refused = false;
  try {
    action();
  } catch (err) {
    refused = true;
  }
  if (!refused) {
    throw new Error('the operation was accepted instead of being refused');
  }
}

async function mustReject(action: () => Promise<void>): Promise<void> {
  try {
    await action();
  } catch (err) {
    return;
  }
  throw new Error('the operation was accepted instead of being refused');
}

function resetMode(): void {
  setUpdateMode('none');
  delete process.env['UPDATE_SNAPSHOTS'];
}

const cases: Case[] = [];

// ---------------------------------------------------------------------------
// File-snapshot assertions: a caller path must not reach outside the project
// ---------------------------------------------------------------------------

cases.push({
  id: 'S1-absolute-outside-create',
  name: 'an absolute snapshot path outside the project creates nothing there',
  run() {
    const dir = outside('snapsec-abs-');
    const target = path.join(dir, 'attack.snap');
    try {
      setUpdateMode('all');
      mustThrow(() => expect('payload').toMatchFileSnapshot(target));
      if (fs.existsSync(target)) {
        throw new Error('a file was created outside the project');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S2-absolute-outside-overwrite',
  name: 'an existing file outside the project keeps its content',
  run() {
    const dir = outside('snapsec-ow-');
    const target = path.join(dir, 'victim.snap');
    try {
      fs.writeFileSync(target, 'ORIGINAL-CONTENT', 'utf-8');
      setUpdateMode('all');
      mustThrow(() => expect('ATTACKER-CONTENT').toMatchFileSnapshot(target));
      if (fs.readFileSync(target, 'utf-8') !== 'ORIGINAL-CONTENT') {
        throw new Error('the file outside the project was overwritten');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S3-relative-traversal-create',
  name: 'a relative snapshot path cannot climb out of the project',
  run() {
    const dir = outside('snapsec-rel-');
    const target = path.relative(process.cwd(), path.join(dir, 'escape.snap'));
    try {
      setUpdateMode('all');
      mustThrow(() => expect('payload').toMatchFileSnapshot(target));
      if (fs.existsSync(path.join(dir, 'escape.snap'))) {
        throw new Error('a file was created outside the project');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S4-outside-compare-content',
  name: 'comparing against a file outside the project does not expose its content',
  run() {
    const dir = outside('snapsec-read-');
    const target = path.join(dir, 'secret.snap');
    const marker = `SECRET-${crypto.randomUUID()}`;
    try {
      fs.writeFileSync(target, JSON.stringify(marker), 'utf-8');
      setUpdateMode('none');
      let message = '';
      let refused = false;
      try {
        expect('different-value').toMatchFileSnapshot(target);
      } catch (err) {
        refused = true;
        message = err instanceof Error ? err.message : String(err);
      }
      if (!refused) {
        throw new Error('the outside file was read without a refusal');
      }
      if (message.includes(marker)) {
        throw new Error('the refusal repeated content read outside the project');
      }
      if (!fs.existsSync(target)) {
        throw new Error('the file outside the project was removed');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S5-link-inside-project',
  name: 'a link inside the project does not carry a write outside it',
  run() {
    const dir = outside('snapsec-link-');
    const linkHome = projectDir('snapseclink-');
    try {
      fs.symlinkSync(dir, path.join(linkHome, 'link'), 'dir');
      const target = path.join(linkHome, 'link', 'through.snap');
      setUpdateMode('all');
      mustThrow(() => expect('payload').toMatchFileSnapshot(target));
      if (fs.existsSync(path.join(dir, 'through.snap'))) {
        throw new Error('a file was created outside the project through a link');
      }
    } finally {
      resetMode();
      fs.rmSync(linkHome, { recursive: true, force: true });
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S6-outside-parent-not-created',
  name: 'a refused snapshot does not create directories outside the project',
  run() {
    const dir = outside('snapsec-mkdir-');
    const parent = path.join(dir, 'newparent');
    const target = path.join(parent, 'sub', 'attack.snap');
    try {
      setUpdateMode('all');
      mustThrow(() => expect('payload').toMatchFileSnapshot(target));
      if (fs.existsSync(parent)) {
        throw new Error('a directory was created outside the project');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

// ---------------------------------------------------------------------------
// Snapshot store: writes stay inside the directory the store was given
// ---------------------------------------------------------------------------

cases.push({
  id: 'S7-store-client-write',
  name: 'a snapshot client does not write outside the configured snapshot directory',
  async run() {
    const base = outside('snapsec-client-');
    const snapDir = path.join(base, 'snaps');
    fs.mkdirSync(snapDir, { recursive: true });
    const target = path.join(base, 'outside.snap');
    try {
      const client = new SnapshotClient(new NodeSnapshotEnvironment('1', snapDir));
      await client.loadSnapshots(target);
      client.prepareTest('case');
      client.assert('value', 'key');
      await mustReject(() => client.saveSnapshots());
      if (fs.existsSync(target)) {
        throw new Error('the snapshot store wrote outside its directory');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S8-store-manager-write',
  name: 'the snapshot coordinator does not write outside the configured snapshot directory',
  async run() {
    const base = outside('snapsec-manager-');
    const snapDir = path.join(base, 'snaps');
    fs.mkdirSync(snapDir, { recursive: true });
    const target = path.join(base, 'outside-manager.snap');
    try {
      const manager = new SnapshotManager(new NodeSnapshotEnvironment('1', snapDir));
      const client = manager.getClient('/somewhere/managed.test.ts');
      await client.loadSnapshots(target);
      client.prepareTest('case');
      client.assert('value', 'key');
      await mustReject(() => manager.finishFile('/somewhere/managed.test.ts'));
      if (fs.existsSync(target)) {
        throw new Error('the snapshot store wrote outside its directory');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S9-store-environment-write',
  name: 'the snapshot environment does not write outside the configured snapshot directory',
  async run() {
    const base = outside('snapsec-env-');
    const snapDir = path.join(base, 'snaps');
    fs.mkdirSync(snapDir, { recursive: true });
    const target = path.join(base, 'outside-env.snap');
    try {
      const env = new NodeSnapshotEnvironment('1', snapDir);
      await mustReject(() => env.saveSnapshotFile(target, 'payload'));
      if (fs.existsSync(target)) {
        throw new Error('the snapshot environment wrote outside its directory');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S10-store-outside-parent-not-created',
  name: 'a refused store write does not create directories outside the snapshot directory',
  async run() {
    const base = outside('snapsec-envmk-');
    const snapDir = path.join(base, 'snaps');
    fs.mkdirSync(snapDir, { recursive: true });
    const parent = path.join(base, 'newparent');
    const target = path.join(parent, 'sub', 'attack.snap');
    try {
      const env = new NodeSnapshotEnvironment('1', snapDir);
      await mustReject(() => env.saveSnapshotFile(target, 'payload'));
      if (fs.existsSync(parent)) {
        throw new Error('a directory was created outside the snapshot directory');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

// ---------------------------------------------------------------------------
// Snapshot store: deletion stays inside the directory the store was given
// ---------------------------------------------------------------------------

cases.push({
  id: 'S11-store-remove-outside',
  name: 'the snapshot store does not remove a file outside its directory',
  async run() {
    const base = outside('snapsec-rm-');
    const snapDir = path.join(base, 'snaps');
    fs.mkdirSync(snapDir, { recursive: true });
    const target = path.join(base, 'victim.snap');
    try {
      fs.writeFileSync(target, 'data', 'utf-8');
      const env = new NodeSnapshotEnvironment('1', snapDir);
      await mustReject(() => env.removeSnapshotFile(target));
      if (!fs.existsSync(target)) {
        throw new Error('a file outside the snapshot directory was removed');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'S12-store-remove-through-link',
  name: 'a link inside the snapshot directory does not carry a removal outside it',
  async run() {
    const base = outside('snapsec-rmlink-');
    const snapDir = path.join(base, 'snaps');
    const outsideDir = path.join(base, 'outside');
    fs.mkdirSync(snapDir, { recursive: true });
    fs.mkdirSync(outsideDir, { recursive: true });
    const victim = path.join(outsideDir, 'victim.snap');
    try {
      fs.writeFileSync(victim, 'data', 'utf-8');
      fs.symlinkSync(outsideDir, path.join(snapDir, 'link'), 'dir');
      const env = new NodeSnapshotEnvironment('1', snapDir);
      await mustReject(() =>
        env.removeSnapshotFile(path.join(snapDir, 'link', 'victim.snap')),
      );
      if (!fs.existsSync(victim)) {
        throw new Error('a file outside the snapshot directory was removed');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

export { cases };
