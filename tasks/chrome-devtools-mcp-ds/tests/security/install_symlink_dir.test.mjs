import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('a path inside a workspace root that is a link to an outside directory', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('is not handed to the browser when an extension is installed', async () => {
    const outsideExtension = path.join(sandbox.outside, 'extension');
    await fs.mkdir(outsideExtension);
    await fs.symlink(outsideExtension, path.join(sandbox.root, 'linked-ext'));

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('install_extension', {
      path: path.join(sandbox.root, 'linked-ext'),
    });

    assert.equal(
      isError(result),
      true,
      `expected a client error, got: ${resultText(result)}`,
    );
    assert.deepEqual(
      mcp.calls.installExtension,
      [],
      'the browser was asked to load a location outside the roots',
    );
  });
});
