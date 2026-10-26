import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

const STATS_MARKER = 'OUTSIDE-STATS-3f91';
const STATIC_MARKER = 'OUTSIDE-STATIC-7c04';

describe('summary data the server reuses from beside a memory snapshot', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('is not read from an outside file when the reusable copy is a link', async () => {
    const snapshot = path.join(sandbox.root, 'profile.heapsnapshot');
    await fs.writeFile(snapshot, 'not a heap snapshot');

    await fs.writeFile(
      path.join(sandbox.outside, 'stats.json'),
      JSON.stringify({nodeCount: 11, marker: STATS_MARKER}),
    );
    await fs.writeFile(
      path.join(sandbox.outside, 'static.json'),
      JSON.stringify({nodeCount: 11, marker: STATIC_MARKER}),
    );
    await fs.symlink(
      path.join(sandbox.outside, 'stats.json'),
      `${snapshot}.stats-cache.json`,
    );
    await fs.symlink(
      path.join(sandbox.outside, 'static.json'),
      `${snapshot}.static-data-cache.json`,
    );

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('get_heapsnapshot_summary', {
      filePath: snapshot,
    });
    const text = resultText(result);

    assert.equal(
      isError(result),
      true,
      `expected a client error, got: ${text}`,
    );
    assert.equal(text.includes(STATS_MARKER), false, 'outside data was read');
    assert.equal(text.includes(STATIC_MARKER), false, 'outside data was read');
  });
});
