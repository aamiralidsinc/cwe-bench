import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('reloading an extension the browser reports', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('does not hand an outside location to the browser', async () => {
    const outsideExtension = path.join(sandbox.outside, 'stored-extension');
    await fs.mkdir(outsideExtension);

    const mcp = await makeMcp({
      extensions: [{id: 'stored-id', name: 'stored', path: outsideExtension}],
    });
    mcp.setRootDir(sandbox.root);

    const result = await mcp.call('reload_extension', {id: 'stored-id'});

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
