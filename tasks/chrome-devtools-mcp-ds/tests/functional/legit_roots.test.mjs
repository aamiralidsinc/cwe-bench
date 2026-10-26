import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {after, before, describe, it} from 'node:test';

import {exists, isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

describe('workspace roots as the client may declare them', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('accepts a root that is itself reached through a link', async () => {
    const realRoot = path.join(sandbox.base, 'real-workspace');
    const linkedRoot = path.join(sandbox.base, 'linked-workspace');
    await fs.mkdir(realRoot);
    await fs.symlink(realRoot, linkedRoot);

    const mcp = await makeMcp();
    mcp.setRootDir(linkedRoot);
    const result = await mcp.call('take_screenshot', {
      filePath: path.join(linkedRoot, 'linked-root.png'),
      format: 'png',
    });

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.equal(
      await exists(path.join(realRoot, 'linked-root.png')),
      true,
      'the output file was not created',
    );
  });

  it('keeps working when one declared root cannot be resolved', async () => {
    const mcp = await makeMcp();
    mcp.context.setRoots([
      {
        uri: pathToFileURL(path.join(sandbox.base, 'not-there-at-all')).href,
        name: 'stale',
      },
      {uri: pathToFileURL(sandbox.root).href, name: 'workspace'},
    ]);

    const result = await mcp.call('take_screenshot', {
      filePath: path.join(sandbox.root, 'with-stale-root.png'),
      format: 'png',
    });

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${resultText(result)}`,
    );
    assert.equal(await exists(path.join(sandbox.root, 'with-stale-root.png')), true);
  });

  it('allows any path when the client declares no roots at all', async () => {
    const mcp = await makeMcp();
    mcp.context.setRoots(undefined);
    const target = path.join(sandbox.outside, 'undeclared.png');

    const result = await mcp.call('take_screenshot', {
      filePath: target,
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
