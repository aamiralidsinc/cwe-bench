// Ordinary use of the primary S3 media handler: a legitimate upload key, a
// literal percent sign in a name, an inner ".." that stays inside, deleting an
// item the listing returned, and listing the root / a directory.
import { beforeEach, describe, expect, it } from 'vitest';
import { createMediaHandler } from '@app/packages/next-tinacms-s3/src/handlers';
import { s3 } from '../support/stubs/aws-s3';
import { resetStubs, makeRes, pagesReq, sentInputs } from '../support/harness';

function handler() {
  return createMediaHandler({
    config: { region: 'us-east-1' },
    bucket: 'private-bucket',
    mediaRoot: 'media',
    authorized: async () => true,
  } as any);
}

async function request(method: string, query: Record<string, any>) {
  const res = makeRes();
  await handler()(pagesReq(method, query), res);
  return res;
}

const deletedKeys = () =>
  sentInputs('DeleteObject').map((input) => String(input.Key));
const prefixes = () =>
  sentInputs('ListObjects').map((input) => String(input.Prefix));

beforeEach(resetStubs);

describe('legitimate presigned uploads', () => {
  it('mints an upload url for a nested key', async () => {
    const res = await request('GET', { key: 'photos/summer/a.png' });
    expect(res.statusCode).toBe(200);
    expect(s3.presigns).toHaveLength(1);
    expect(String(res.body.signedUrl)).toBeTruthy();
    expect(String(res.body.src)).toContain('a.png');
  });

  it('accepts a name containing a literal percent sign', async () => {
    const res = await request('GET', { key: 'photos/100%off.png' });
    expect(res.statusCode).toBe(200);
    expect(s3.presigns).toHaveLength(1);
  });

  it('accepts an inner parent segment that stays inside the root', async () => {
    const res = await request('GET', { key: 'photos/../a.png' });
    expect(res.statusCode).toBe(200);
    expect(s3.presigns).toHaveLength(1);
  });
});

describe('legitimate delete and listing', () => {
  it('deletes the identifier the listing returned, without re-prefixing it', async () => {
    s3.listResult = {
      Contents: [{ Key: 'media/photos/a.png' }],
      CommonPrefixes: [],
    };
    const listed = await request('GET', { directory: 'photos' });
    expect(listed.statusCode).toBe(200);
    expect(listed.body.items[0].id).toBe('media/photos/a.png');

    const removed = await request('DELETE', {
      media: ['media', listed.body.items[0].id],
    });
    expect(removed.statusCode).toBe(200);
    expect(deletedKeys()).toEqual(['media/photos/a.png']);
  });

  it('deletes a relative key given inside the root', async () => {
    const res = await request('DELETE', { media: ['media', 'photos/a.png'] });
    expect(res.statusCode).toBe(200);
    expect(deletedKeys()).toHaveLength(1);
    expect(deletedKeys()[0].endsWith('photos/a.png')).toBe(true);
  });

  it('lists the root of the media area', async () => {
    const res = await request('GET', {});
    expect(res.statusCode).toBe(200);
    expect(prefixes()).toEqual(['media/']);
  });

  it('lists a directory with leading and trailing slashes', async () => {
    const res = await request('GET', { directory: '/photos/' });
    expect(res.statusCode).toBe(200);
    expect(prefixes()).toEqual(['media/photos/']);
  });

  it('treats an empty key as a listing request', async () => {
    const res = await request('GET', { key: '' });
    expect(res.statusCode).toBe(200);
    expect(s3.presigns).toHaveLength(0);
    expect(prefixes()).toHaveLength(1);
  });
});
