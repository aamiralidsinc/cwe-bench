// The multi-select delete route shipped next to the main S3 media handler. It
// takes an array of caller-chosen keys; all of them must stay inside the
// configured media root.
import { beforeEach, describe, it } from 'vitest';
import { createBatchDeleteHandler } from '@app/packages/next-tinacms-s3/src/batch-delete';
import {
  resetStubs,
  makeRes,
  pagesReq,
  sentInputs,
  expectRefused,
  expectConfined,
} from '../support/harness';

const ROOT = 'media';

function handler() {
  return createBatchDeleteHandler({
    config: { region: 'us-east-1' },
    bucket: 'private-bucket',
    mediaRoot: ROOT,
    authorized: async () => true,
  } as any);
}

function deletedKeys(): string[] {
  const keys: string[] = [];
  for (const input of sentInputs('DeleteObjects')) {
    for (const object of input.Delete?.Objects ?? []) {
      keys.push(String(object.Key));
    }
  }
  return keys;
}

async function remove(keys: any) {
  const res = makeRes();
  await handler()(pagesReq('DELETE', { keys }), res);
  return res;
}

beforeEach(resetStubs);

describe('batch delete is confined to the media root', () => {
  it('refuses a key that walks above the root', async () => {
    const res = await remove(['../secrets.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an inner climb that leaves the root', async () => {
    const res = await remove(['a/../../outside.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an absolute key', async () => {
    const res = await remove(['/etc/passwd']);
    expectRefused(res, deletedKeys());
  });

  it('refuses a windows-style separator', async () => {
    const res = await remove(['..\\outside.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses the whole batch when one key is invalid', async () => {
    const res = await remove(['media/photos/a.png', '../outside.png']);
    expectRefused(res, deletedKeys());
  });

  it('never deletes a batch key outside the root', async () => {
    const res = await remove(['media/photos/a.png', 'private/config.json']);
    expectConfined(res, deletedKeys(), ROOT);
  });
});
