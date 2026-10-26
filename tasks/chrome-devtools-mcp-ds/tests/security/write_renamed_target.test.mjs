import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {isError, makeMcp, makeSandbox, readIfExists, resultText} from '../support/harness.mjs';

const ORIGINAL = 'ORIGINAL-CONTENT-5512';

describe('output named by the server with a different extension than the caller gave', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('is not written through a link at the name the server uses', async () => {
    const victim = path.join(sandbox.outside, 'report.txt');
    await fs.writeFile(victim, ORIGINAL);
    await fs.symlink(victim, path.join(sandbox.root, 'report.png'));

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'report.txt'),
      format: 'png',
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
  });
});
