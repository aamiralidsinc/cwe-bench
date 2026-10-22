// The app-router variant of the S3 media handlers. It exposes the same
// presign / direct-upload / delete / list operations through a different
// module, so the same confinement must hold there too.
import { beforeEach, describe, it } from 'vitest';
import { createMediaHandlers } from '@app/packages/next-tinacms-s3/src/app-handlers';
import {
  resetStubs,
  presignedKeys,
  sentInputs,
  expectRefused,
  expectConfined,
} from '../support/harness';

const ROOT = 'media';

function handlers(mediaRoot: string = ROOT) {
  return createMediaHandlers({
    config: { region: 'us-east-1' },
    bucket: 'private-bucket',
    mediaRoot,
    authorized: async () => true,
  } as any);
}

const putKeys = () => sentInputs('PutObject').map((input) => String(input.Key));
const deleteKeys = () =>
  sentInputs('DeleteObject').map((input) => String(input.Key));
const prefixes = () =>
  sentInputs('ListObjects').map((input) => String(input.Prefix));

function get(query: string) {
  return handlers().GET(new Request(`http://localhost/api/media?${query}`) as any);
}

function put(query: string) {
  return handlers().POST(
    new Request(`http://localhost/api/media?${query}`, {
      method: 'POST',
      body: 'DATA',
      headers: { 'content-type': 'image/png' },
    }) as any
  );
}

function remove(media: any[]) {
  return handlers().DELETE(new Request('http://localhost/api/media') as any, {
    params: { media },
  } as any);
}

beforeEach(resetStubs);

describe('app-router presigned upload is confined to the media root', () => {
  it('refuses an absolute key', async () => {
    const res = await get('key=%2Fetc%2Fpasswd');
    expectRefused(res as any, presignedKeys());
  });

  it('refuses a key that walks above the root', async () => {
    const res = await get('key=..%2Foutside.png');
    expectRefused(res as any, presignedKeys());
  });

  it('never mints a url for a bucket key outside the root', async () => {
    const res = await get('key=private%2Fconfig.json');
    expectConfined(res as any, presignedKeys(), ROOT);
  });
});

describe('app-router direct upload is confined to the media root', () => {
  it('refuses a key that walks above the root', async () => {
    const res = await put('key=..%2Foutside.png');
    expectRefused(res as any, putKeys());
  });

  it('never writes a bucket key outside the root', async () => {
    const res = await put('key=private%2Fconfig.json');
    expectConfined(res as any, putKeys(), ROOT);
  });
});

describe('app-router delete is confined to the media root', () => {
  it('refuses a key that walks above the root', async () => {
    const res = await remove(['media', '../secret.png']);
    expectRefused(res as any, deleteKeys());
  });

  it('never deletes a bucket key outside the root', async () => {
    const res = await remove(['media', 'private/config.json']);
    expectConfined(res as any, deleteKeys(), ROOT);
  });
});

describe('app-router listing is confined to the media root', () => {
  it('refuses a directory that walks above the root', async () => {
    const res = await get('directory=..%2F');
    expectRefused(res as any, prefixes());
  });

  it('refuses a windows-style separator', async () => {
    const res = await get(`directory=${encodeURIComponent('..\\outside')}`);
    expectRefused(res as any, prefixes());
  });
});
