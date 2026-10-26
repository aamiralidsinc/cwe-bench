import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {exists, isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('a path inside a workspace root that is a link to an outside directory', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('is not followed when the server writes captured output', async () => {
    await fs.symlink(sandbox.outside, path.join(sandbox.root, 'captures'));
    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);

    const target = path.join(sandbox.outside, 'captured.png');
    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'captures', 'captured.png'),
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
