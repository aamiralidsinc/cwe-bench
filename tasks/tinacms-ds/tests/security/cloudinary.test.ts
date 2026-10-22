// The Cloudinary media handler. It has no media-root option, but a
// caller-supplied upload folder / filename, public id or listing directory must
// still be relative and must never climb above the area it serves.
import { beforeEach, describe, it } from 'vitest';
import { createMediaHandler } from '@app/packages/next-tinacms-cloudinary/src/handlers';
import { state as cloudinary } from '../support/stubs/cloudinary';
import { resetStubs, makeRes, pagesReq, expectRefused } from '../support/harness';

function handler() {
  return createMediaHandler({
    cloud_name: 'demo',
    api_key: 'key',
    api_secret: 'secret',
    authorized: async () => true,
  } as any);
}

async function upload(directory: any, originalname = 'a.png') {
  const res = makeRes();
  await handler()(
    pagesReq('POST', {}, {
      body: { directory },
      file: { path: '/tmp/upload', originalname, mimetype: 'image/png' },
    }),
    res
  );
  return res;
}

async function remove(media: any[]) {
  const res = makeRes();
  await handler()(pagesReq('DELETE', { media }), res);
  return res;
}

async function list(directory: any) {
  const res = makeRes();
  await handler()(pagesReq('GET', { directory }), res);
  return res;
}

beforeEach(resetStubs);

describe('cloudinary upload is confined to the served area', () => {
  it('refuses a folder that walks upward', async () => {
    const res = await upload('../outside');
    expectRefused(res, cloudinary.uploads);
  });

  it('refuses an inner climb that leaves the area', async () => {
    const res = await upload('a/../../../outside');
    expectRefused(res, cloudinary.uploads);
  });

  it('refuses a leading-slash traversal folder', async () => {
    const res = await upload('/../outside');
    expectRefused(res, cloudinary.uploads);
  });

  it('refuses a folder containing a NUL byte', async () => {
    const res = await upload('../\u0000outside');
    expectRefused(res, cloudinary.uploads);
  });

  it('refuses a filename that walks upward', async () => {
    const res = await upload('photos', '../evil.png');
    expectRefused(res, cloudinary.uploads);
  });
});

describe('cloudinary delete is confined to the served area', () => {
  it('refuses a public id that walks upward', async () => {
    const res = await remove(['media', '../secret']);
    expectRefused(res, cloudinary.destroys);
  });

  it('refuses an absolute public id', async () => {
    const res = await remove(['media', '/etc/passwd']);
    expectRefused(res, cloudinary.destroys);
  });

  it('refuses an empty public id', async () => {
    const res = await remove(['media', '']);
    expectRefused(res, cloudinary.destroys);
  });
});

describe('cloudinary listing is confined to the served area', () => {
  it('refuses a directory that walks upward', async () => {
    const res = await list('../');
    expectRefused(res, cloudinary.searches);
  });

  it('refuses an inner climb that leaves the area', async () => {
    const res = await list('a/../../outside');
    expectRefused(res, cloudinary.searches);
  });

  it('refuses a windows-style separator', async () => {
    const res = await list('..\\outside');
    expectRefused(res, cloudinary.searches);
  });
});
