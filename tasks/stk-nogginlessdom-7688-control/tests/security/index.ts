// Control security cases: only the advisory's own route, a file-snapshot
// assertion whose caller-supplied path reaches outside the project.
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import { expect, setUpdateMode } from '../support/product.ts';
import type { Case } from '../support/runner.ts';

function outside(prefix: string): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
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

function resetMode(): void {
  setUpdateMode('none');
  delete process.env['UPDATE_SNAPSHOTS'];
}

const cases: Case[] = [];

cases.push({
  id: 'C1-absolute-outside-create',
  name: 'an absolute snapshot path outside the project creates nothing there',
  run() {
    const dir = outside('snapctl-abs-');
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
  id: 'C2-absolute-outside-overwrite',
  name: 'an existing file outside the project keeps its content',
  run() {
    const dir = outside('snapctl-ow-');
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
  id: 'C3-relative-traversal-create',
  name: 'a relative snapshot path cannot climb out of the project',
  run() {
    const dir = outside('snapctl-rel-');
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

export { cases };
