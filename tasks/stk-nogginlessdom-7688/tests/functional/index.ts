// Functional cases: the documented snapshot behaviour keeps working, including
// the legitimate values that sit next to the hidden routes (a store pointed at
// its own directory outside the project, and the default store layout).
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import {
  expect,
  serialize,
  setUpdateMode,
  SnapshotClient,
  NodeSnapshotEnvironment,
  SnapshotManager,
} from '../support/product.ts';
import type { Case } from '../support/runner.ts';

function projectDir(prefix: string): string {
  return fs.mkdtempSync(path.join(process.cwd(), prefix));
}

function outside(prefix: string): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function resetMode(): void {
  setUpdateMode('none');
  delete process.env['UPDATE_SNAPSHOTS'];
}

const cases: Case[] = [];

cases.push({
  id: 'F1-create-inside-project',
  name: 'a new file snapshot inside the project is created with the serialized value',
  run() {
    const dir = projectDir('snapfn-');
    try {
      const target = path.join(dir, 'created.snap');
      setUpdateMode('all');
      expect({ name: 'created', count: 3 }).toMatchFileSnapshot(target);
      if (!fs.existsSync(target)) throw new Error('the snapshot file was not created');
      if (fs.readFileSync(target, 'utf-8') !== serialize({ name: 'created', count: 3 })) {
        throw new Error('the snapshot file does not hold the serialized value');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F2-create-nested-inside-project',
  name: 'a new file snapshot creates its missing directories inside the project',
  run() {
    const dir = projectDir('snapfn-nest-');
    try {
      const target = path.join(dir, 'group', 'deep', 'nested.snap');
      setUpdateMode('all');
      expect('nested-value').toMatchFileSnapshot(target);
      if (!fs.existsSync(target)) throw new Error('the nested snapshot file was not created');
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F3-match-existing-inside-project',
  name: 'an existing file snapshot inside the project matches its stored value',
  run() {
    const dir = projectDir('snapfn-match-');
    try {
      const target = path.join(dir, 'stored.snap');
      fs.writeFileSync(target, serialize({ same: true }), 'utf-8');
      setUpdateMode('none');
      expect({ same: true }).toMatchFileSnapshot(target);
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F4-mismatch-inside-project',
  name: 'a differing value inside the project reports a snapshot mismatch',
  run() {
    const dir = projectDir('snapfn-mismatch-');
    try {
      const target = path.join(dir, 'stored.snap');
      fs.writeFileSync(target, serialize('old'), 'utf-8');
      setUpdateMode('none');
      let message = '';
      try {
        expect('new').toMatchFileSnapshot(target);
      } catch (err) {
        message = err instanceof Error ? err.message : String(err);
      }
      if (!/mismatch/i.test(message)) {
        throw new Error('the mismatch was not reported as a snapshot mismatch');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F5-overwrite-inside-project',
  name: 'update mode overwrites an existing file snapshot inside the project',
  run() {
    const dir = projectDir('snapfn-update-');
    try {
      const target = path.join(dir, 'stored.snap');
      fs.writeFileSync(target, serialize('old'), 'utf-8');
      setUpdateMode('all');
      expect('new').toMatchFileSnapshot(target);
      if (fs.readFileSync(target, 'utf-8') !== serialize('new')) {
        throw new Error('the snapshot file was not overwritten in update mode');
      }
    } finally {
      resetMode();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F6-store-directory-outside-project',
  name: 'a snapshot store pointed at its own directory writes, reads and removes there',
  async run() {
    const base = outside('snapfn-store-');
    const snapDir = path.join(base, 'snap-root');
    fs.mkdirSync(snapDir, { recursive: true });
    try {
      const env = new NodeSnapshotEnvironment('1', snapDir);
      const resolved = env.resolveSnapshotPath('/somewhere/example.test.ts');
      if (resolved !== path.join(snapDir, 'example.test.snap')) {
        throw new Error(`unexpected resolved path: ${resolved}`);
      }
      await env.saveSnapshotFile(resolved, 'stored-content');
      if ((await env.readSnapshotFile(resolved)) !== 'stored-content') {
        throw new Error('the stored snapshot could not be read back');
      }
      await env.removeSnapshotFile(resolved);
      if (fs.existsSync(resolved)) {
        throw new Error('the stored snapshot could not be removed');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F7-store-cleanup-removes-obsolete',
  name: 'cleanup removes an obsolete snapshot inside the store directory',
  async run() {
    const base = outside('snapfn-cleanup-');
    const snapDir = path.join(base, 'snap-root');
    fs.mkdirSync(snapDir, { recursive: true });
    try {
      const env = new NodeSnapshotEnvironment('1', snapDir);
      const resolved = env.resolveSnapshotPath('/somewhere/obsolete.test.ts');
      await env.saveSnapshotFile(resolved, 'obsolete');
      const manager = new SnapshotManager(env);
      manager.getClient('/somewhere/obsolete.test.ts');
      await manager.cleanup();
      if (fs.existsSync(resolved)) {
        throw new Error('the obsolete snapshot was not removed');
      }
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F8-default-store-layout',
  name: 'the default store layout still writes and removes where it is pointed',
  async run() {
    const base = outside('snapfn-default-');
    const target = path.join(base, '__snapshots__', 'legacy.snap');
    try {
      const env = new NodeSnapshotEnvironment();
      await env.saveSnapshotFile(target, 'legacy-content');
      if (!fs.existsSync(target)) throw new Error('the default store did not write');
      if ((await env.readSnapshotFile(target)) !== 'legacy-content') {
        throw new Error('the default store could not read the file back');
      }
      await env.removeSnapshotFile(target);
      if (fs.existsSync(target)) throw new Error('the default store did not remove the file');
    } finally {
      fs.rmSync(base, { recursive: true, force: true });
    }
  },
});

cases.push({
  id: 'F9-inline-snapshot-write-and-match',
  name: 'a keyed snapshot is written next to the test and then matches',
  run() {
    const snapDir = path.join(import.meta.dir, '__snapshots__');
    try {
      fs.rmSync(snapDir, { recursive: true, force: true });
      setUpdateMode('none');
      expect({ inline: 'value' }).toMatchSnapshot('functional key');
      expect({ inline: 'value' }).toMatchSnapshot('functional key');
      if (!fs.existsSync(snapDir)) {
        throw new Error('the keyed snapshot file was not created');
      }
    } finally {
      resetMode();
      fs.rmSync(snapDir, { recursive: true, force: true });
    }
  },
});

export { cases };
