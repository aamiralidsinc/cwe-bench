import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {exists, isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('temporary output and extensions that live inside the workspace', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('still writes scratch output into the temporary area', async () => {
    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const {filepath} = await mcp.context.saveTemporaryFile(
      new TextEncoder().encode('scratch'),
      'scratch.png',
    );
    try {
      const realTmp = await fs.realpath(os.tmpdir());
      const realFile = await fs.realpath(path.dirname(filepath));
      assert.equal(
        realFile === realTmp || realFile.startsWith(realTmp + path.sep),
        true,
        `temporary output landed outside the temporary area: ${filepath}`,
      );
      assert.equal(await exists(filepath), true);
    } finally {
      await fs.rm(path.dirname(filepath), {recursive: true, force: true});
    }
  });

  it('still attaches a screenshot when the caller gives no path', async () => {
    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('take_screenshot', {
      format: 'png',
    });

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.equal(
      (result.content ?? []).some(part => part.type === 'image'),
      true,
      'the screenshot was not attached',
    );
  });

  it('still installs an extension from inside the workspace', async () => {
    const insideExtension = path.join(sandbox.root, 'inside-extension');
    await fs.mkdir(insideExtension);

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('install_extension', {
      path: insideExtension,
    });

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.deepEqual(mcp.calls.installExtension, [insideExtension]);
  });

  it('still reloads an extension that lives inside the workspace', async () => {
    const insideExtension = path.join(sandbox.root, 'reloaded-extension');
    await fs.mkdir(insideExtension);

    const mcp = await makeMcp({
      extensions: [{id: 'inside-id', name: 'inside', path: insideExtension}],
    });
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('reload_extension', {id: 'inside-id'});

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.deepEqual(mcp.calls.installExtension, [insideExtension]);
  });
});
