// Ordinary use of the three sibling routes: batch delete of listed
// identifiers, the app-router media operations, and a copy between two
// in-root keys.
import { beforeEach, describe, expect, it } from 'vitest';
import { createBatchDeleteHandler } from '@app/packages/next-tinacms-s3/src/batch-delete';
import { createMediaHandlers as createAppHandlers } from '@app/packages/next-tinacms-s3/src/app-handlers';
import { createCopyHandler } from '@app/packages/next-tinacms-dos/src/copy-handler';
import { s3 } from '../support/stubs/aws-s3';
import {
  resetStubs,
  makeRes,
  pagesReq,
  sentInputs,
} from '../support/harness';

const s3Config = {
  config: { region: 'us-east-1' },
  bucket: 'private-bucket',
  mediaRoot: 'media',
  authorized: async () => true,
} as any;

const dosConfig = {
  config: {
    region: 'us-east-1',
    endpoint: 'https://sfo2.digitaloceanspaces.com',
  },
  bucket: 'private-space',
  mediaRoot: 'media',
  authorized: async () => true,
} as any;

beforeEach(resetStubs);

describe('legitimate batch delete', () => {
  it('deletes several listed identifiers', async () => {
    const res = makeRes();
    await createBatchDeleteHandler(s3Config)(
      pagesReq('DELETE', {
        keys: ['media/photos/a.png', 'media/archive/b.png'],
      }),
      res
    );
    expect(res.statusCode).toBe(200);
    const objects = sentInputs('DeleteObjects')[0].Delete.Objects;
    expect(objects.map((object: any) => object.Key)).toEqual([
      'media/photos/a.png',
      'media/archive/b.png',
    ]);
  });
});

describe('legitimate app-router media use', () => {
  it('mints a presigned upload url for a nested key', async () => {
    const res: any = await createAppHandlers(s3Config).GET(
      new Request('http://localhost/api/media?key=photos%2Fa.png') as any
    );
    expect(res.status).toBe(200);
    expect(s3.presigns).toHaveLength(1);
  });

  it('accepts a direct upload for a nested key', async () => {
    const res: any = await createAppHandlers(s3Config).POST(
      new Request('http://localhost/api/media?key=photos%2Fa.png', {
        method: 'POST',
        body: 'DATA',
      }) as any
    );
    expect(res.status).toBe(200);
    const keys = sentInputs('PutObject').map((input) => String(input.Key));
    expect(keys).toHaveLength(1);
    expect(keys[0].endsWith('photos/a.png')).toBe(true);
  });

  it('deletes a listed identifier', async () => {
    const res: any = await createAppHandlers(s3Config).DELETE(
      new Request('http://localhost/api/media') as any,
      { params: { media: ['media', 'media/photos/a.png'] } } as any
    );
    expect(res.status).toBe(200);
    expect(sentInputs('DeleteObject').map((input) => String(input.Key))).toEqual([
      'media/photos/a.png',
    ]);
  });

  it('lists a directory', async () => {
    const res: any = await createAppHandlers(s3Config).GET(
      new Request('http://localhost/api/media?directory=photos') as any
    );
    expect(res.status).toBe(200);
    expect(
      sentInputs('ListObjects').map((input) => String(input.Prefix))
    ).toEqual(['media/photos/']);
  });
});

describe('legitimate copy', () => {
  it('copies between two in-root keys', async () => {
    const res = makeRes();
    await createCopyHandler(dosConfig)(
      pagesReq('POST', {
        from: 'media/photos/a.png',
        to: 'media/archive/a.png',
      }),
      res
    );
    expect(res.statusCode).toBe(200);
    const input = sentInputs('CopyObject')[0];
    expect(String(input.CopySource)).toBe('private-space/media/photos/a.png');
    expect(String(input.Key)).toBe('media/archive/a.png');
  });
});
