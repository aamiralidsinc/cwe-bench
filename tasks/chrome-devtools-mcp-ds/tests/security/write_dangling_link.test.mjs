import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {exists, isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('a link inside a workspace root whose target does not exist yet', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('does not make the server create the outside target', async () => {
    const target = path.join(sandbox.outside, 'fresh.png');
    await fs.symlink(target, path.join(sandbox.root, 'new-output.png'));

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'new-output.png'),
      format: 'png',
    });

    assert.equal(
      isError(result),
      true,
      `expected a client error, got: ${resultText(result)}`,
    );
    assert.equal(await exists(target), false, 'a file was created outside');
  });

  it('does not make the server create it under the name the server chooses', async () => {
    const target = path.join(sandbox.outside, 'derived.png');
    await fs.symlink(target, path.join(sandbox.root, 'second.png'));

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'second.txt'),
      format: 'png',
    });

    assert.equal(
      isError(result),
      true,
      `expected a client error, got: ${resultText(result)}`,
    );
    assert.equal(await exists(target), false, 'a file was created outside');
  });
});
