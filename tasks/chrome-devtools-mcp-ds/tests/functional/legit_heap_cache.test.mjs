import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {after, before, describe, it} from 'node:test';

import {isError, makeMcp, makeSandbox, resultText} from '../support/harness.mjs';

const STATS_MARKER = 'INSIDE-STATS-19a2';
const STATIC_MARKER = 'INSIDE-STATIC-64b8';

describe('summary data kept beside a memory snapshot inside the workspace', () => {
  let sandbox;

  before(async () => {
    sandbox = await makeSandbox();
  });

  after(async () => {
    await sandbox?.cleanup();
  });

  it('is still reused instead of loading the snapshot again', async () => {
    const snapshot = path.join(sandbox.root, 'kept.heapsnapshot');
    await fs.writeFile(snapshot, 'not a heap snapshot');
    await fs.writeFile(
      `${snapshot}.stats-cache.json`,
      JSON.stringify({nodeCount: 3, marker: STATS_MARKER}),
    );
    await fs.writeFile(
      `${snapshot}.static-data-cache.json`,
      JSON.stringify({nodeCount: 3, marker: STATIC_MARKER}),
    );

    const mcp = await makeMcp();
    mcp.setRootDir(sandbox.root);
    const result = await mcp.call('get_heapsnapshot_summary', {
      filePath: snapshot,
    });
    const text = resultText(result);

    assert.equal(
      isError(result),
      false,
      `expected success, got: ${text}`,
    );
    assert.equal(text.includes(STATS_MARKER), true, 'the summary was not reused');
    assert.equal(text.includes(STATIC_MARKER), true, 'the summary was not reused');
  });
});
