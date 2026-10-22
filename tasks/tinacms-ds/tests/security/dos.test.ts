// The DigitalOcean Spaces media handler: multipart upload, delete and list all
// take caller-chosen keys and must stay inside the configured media root.
import { afterEach, beforeEach, describe, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createMediaHandler } from '@app/packages/next-tinacms-dos/src/handlers';
import {
  resetStubs,
  makeRes,
  pagesReq,
  sentInputs,
  expectRefused,
  expectConfined,
} from '../support/harness';

const ROOT = 'media';
const tmpDirs: string[] = [];

function tempFile(name: string): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dos-media-'));
  tmpDirs.push(dir);
  const file = path.join(dir, name);
  fs.writeFileSync(file, 'DATA');
  return file;
}

function handler(mediaRoot: string = ROOT) {
  return createMediaHandler({
    config: {
      region: 'us-east-1',
      endpoint: 'https://sfo2.digitaloceanspaces.com',
    },
    bucket: 'private-space',
    mediaRoot,
    authorized: async () => true,
  } as any);
}

async function upload(directory: any, filename = 'a.png') {
  const res = makeRes();
  const filePath = tempFile(filename);
  await handler()(
    pagesReq('POST', {}, { body: { directory }, file: { path: filePath, mimetype: 'image/png' } }),
    res
  );
  return res;
}

const putKeys = () => sentInputs('PutObject').map((input) => String(input.Key));
const deletedKeys = () =>
  sentInputs('DeleteObject').map((input) => String(input.Key));
const prefixes = () =>
  sentInputs('ListObjects').map((input) => String(input.Prefix));

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
afterEach(() => {
  while (tmpDirs.length) {
    fs.rmSync(tmpDirs.pop() as string, { recursive: true, force: true });
  }
});

describe('multipart upload is confined to the media root', () => {
  it('refuses a directory that walks above the root', async () => {
    const res = await upload('../outside');
    expectRefused(res, putKeys());
  });

  it('refuses an inner climb that leaves the root', async () => {
    const res = await upload('a/../../../outside');
    expectRefused(res, putKeys());
  });

  it('refuses a windows-style separator', async () => {
    const res = await upload('..\\outside');
    expectRefused(res, putKeys());
  });

  it('refuses a directory containing a NUL byte', async () => {
    const res = await upload('../\u0000outside');
    expectRefused(res, putKeys());
  });
});

describe('delete is confined to the media root', () => {
  it('refuses a key that walks above the root', async () => {
    const res = await deleteKey(['media', '../secret.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses a key split across route segments that walks above the root', async () => {
    const res = await deleteKey(['media', '..', '..', 'secret.png']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an absolute key', async () => {
    const res = await deleteKey(['media', '/etc/passwd']);
    expectRefused(res, deletedKeys());
  });

  it('refuses an empty key', async () => {
    const res = await deleteKey(['media', '']);
    expectRefused(res, deletedKeys());
  });

  it('never deletes a space key outside the root', async () => {
    const res = await deleteKey(['media', 'private/config.json']);
    expectConfined(res, deletedKeys(), ROOT);
  });
});

describe('listing is confined to the media root', () => {
  it('refuses a directory that walks above the root', async () => {
    const res = await listDirectory('..');
    expectRefused(res, prefixes());
  });

  it('refuses a leading-slash traversal directory', async () => {
    const res = await listDirectory('/../x');
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
