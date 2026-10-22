// Ordinary use of the Cloudinary media handler: upload into a folder, delete a
// public id, and list the root / a folder.
import { beforeEach, describe, expect, it } from 'vitest';
import { createMediaHandler } from '@app/packages/next-tinacms-cloudinary/src/handlers';
import { state as cloudinary } from '../support/stubs/cloudinary';
import { resetStubs, makeRes, pagesReq } from '../support/harness';

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

async function request(method: string, query: Record<string, any>) {
  const res = makeRes();
  await handler()(pagesReq(method, query), res);
  return res;
}

beforeEach(resetStubs);

describe('legitimate Cloudinary use', () => {
  it('uploads into a folder', async () => {
    const res = await upload('photos');
    expect(res.statusCode).toBe(200);
    expect(cloudinary.uploads.map((entry) => entry.folder)).toEqual(['photos']);
  });

  it('strips a leading slash from the folder', async () => {
    const res = await upload('/photos');
    expect(res.statusCode).toBe(200);
    expect(cloudinary.uploads.map((entry) => entry.folder)).toEqual(['photos']);
  });

  it('deletes a public id', async () => {
    const res = await request('DELETE', { media: ['media', 'photos/a.png'] });
    expect(res.statusCode).toBe(200);
    expect(cloudinary.destroys).toEqual(['photos/a.png']);
  });

  it('lists the root', async () => {
    const res = await request('GET', {});
    expect(res.statusCode).toBe(200);
    expect(cloudinary.searches).toEqual(['folder=""']);
  });

  it('lists a folder', async () => {
    const res = await request('GET', { directory: 'photos' });
    expect(res.statusCode).toBe(200);
    expect(cloudinary.searches).toEqual(['folder="photos"']);
  });
});
