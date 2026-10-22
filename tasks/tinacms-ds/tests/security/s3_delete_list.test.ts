// The delete and listing branches of the primary S3 media handler. Both take
// a caller-chosen object key / directory and must stay inside the configured
// media root.
import { beforeEach, describe, it } from 'vitest';
import { createMediaHandler } from '@app/packages/next-tinacms-s3/src/handlers';
import {
  resetStubs,
  makeRes,
  pagesReq,
  sentInputs,
  expectRefused,
  expectConfined,
} from '../support/harness';

const ROOT = 'media';

function handler(mediaRoot: string = ROOT) {
  return createMediaHandler({
    config: { region: 'us-east-1' },
    bucket: 'private-bucket',
    mediaRoot,
    authorized: async () => true,
  } as any);
}

const deletedKeys = () =>
  sentInputs('DeleteObject').map((input) => String(input.Key));

async function deleteKey(media: any[]) {
  const res = makeRes();
  await handler()(pagesReq('DELETE', { media }), res);
  return res;
}

async function listDirectory(directory: any) {
  const res = makeRes();
  await handler()(pagesReq('GET', { directory }), res);
  return res;
}

beforeEach(resetStubs);

describe('delete is confined to the media root', () => {
  it('refuses a key that walks above the root', async () => {
    const res = await deleteKey(['media', '../secret.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an absolute key', async () => {
    const res = await deleteKey(['media', '/etc/passwd']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an inner climb that leaves the root', async () => {
    const res = await deleteKey(['media', 'photos/../../outside.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses a windows-style separator', async () => {
    const res = await deleteKey(['media', '..\\outside.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an empty key', async () => {
    const res = await deleteKey(['media', '']);
    expectRefused(res, deletedKeys());
  });

  it('never deletes a bucket key outside the root', async () => {
    const res = await deleteKey(['media', 'private/config.json']);
    expectConfined(res, deletedKeys(), ROOT);
  });
});

describe('listing is confined to the media root', () => {
  const prefixes = () =>
    sentInputs('ListObjects').map((input) => String(input.Prefix));

  it('refuses a directory that walks above the root', async () => {
    const res = await listDirectory('../');
    expectRefused(res, prefixes());
  });

  it('refuses a leading-slash traversal directory', async () => {
    const res = await listDirectory('/../');
    expectRefused(res, prefixes());
  });

  it('refuses an inner climb that leaves the root', async () => {
    const res = await listDirectory('a/../../outside');
    expectRefused(res, prefixes());
  });

  it('refuses a windows-style separator', async () => {
    const res = await listDirectory('..\\outside');
    expectRefused(res, prefixes());
  });
});
