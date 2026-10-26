import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {exists, isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('ordinary saves inside a workspace root', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('creates missing nested directories for a new output file', async () => {
    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const target = path.join(sandbox.root, 'deep', 'nested', 'shot.png');

    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'deep', 'nested', 'shot.txt'),
      format: 'png',
    });

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.equal(await exists(target), true, 'the output file was not created');
  });

  it('writes through a link whose target is also inside the root', async () => {
    await fs.mkdir(path.join(sandbox.root, 'real'));
    await fs.symlink(
      path.join(sandbox.root, 'real'),
      path.join(sandbox.root, 'alias'),
    );

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const target = path.join(sandbox.root, 'real', 'aliased.png');

    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'alias', 'aliased.png'),
      format: 'png',
    });

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.equal(await exists(target), true, 'the output file was not created');
  });
});
