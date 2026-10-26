import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {isError, makeMcp, makeSandbox, readIfExists, resultText} from '../support/harness.mjs';

const ORIGINAL = 'ORIGINAL-CONTENT-8823';

describe('a memory snapshot saved under the name the server chooses', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('is not written through a link at the name the server uses', async () => {
    const victim = path.join(sandbox.outside, 'store.bin');
    await fs.writeFile(victim, ORIGINAL);
    await fs.symlink(victim, path.join(sandbox.root, 'capture.heapsnapshot'));

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('take_heapsnapshot', {
      filePath: path.join(sandbox.root, 'capture.txt'),
    });

    assert.equal(
      isError(result),
      true,
      `expected a client error, got: ${resultText(result)}`,
    );
    assert.equal(
      await readIfExists(victim),
      ORIGINAL,
      'a file outside the roots was changed',
    );
    assert.deepEqual(
      mcp.calls.captureHeapSnapshot,
      [],
      'the browser was asked to write outside the roots',
    );
  });
});
