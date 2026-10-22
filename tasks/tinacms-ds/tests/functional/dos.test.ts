// Ordinary use of the DigitalOcean Spaces media handler: multipart uploads in
// a directory, literal percent names, deleting a listed identifier and
// deleting a key split across route segments, and listing.
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createMediaHandler } from '@app/packages/next-tinacms-dos/src/handlers';
import { resetStubs, makeRes, pagesReq, sentInputs } from '../support/harness';

const tmpDirs: string[] = [];

function tempFile(name: string): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dos-legit-'));
  tmpDirs.push(dir);
  const file = path.join(dir, name);
  fs.writeFileSync(file, 'DATA');
  return file;
}

function handler() {
  return createMediaHandler({
    config: {
      region: 'us-east-1',
      endpoint: 'https://sfo2.digitaloceanspaces.com',
    },
    bucket: 'private-space',
    mediaRoot: 'media',
    authorized: async () => true,
  } as any);
}

async function upload(directory: any, filename = 'a.png') {
  const res = makeRes();
  await handler()(
    pagesReq('POST', {}, {
      body: { directory },
      file: { path: tempFile(filename), mimetype: 'image/png' },
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

const putKeys = () => sentInputs('PutObject').map((input) => String(input.Key));
const deletedKeys = () =>
  sentInputs('DeleteObject').map((input) => String(input.Key));
const prefixes = () =>
  sentInputs('ListObjects').map((input) => String(input.Prefix));

beforeEach(resetStubs);
afterEach(() => {
  while (tmpDirs.length) {
    fs.rmSync(tmpDirs.pop() as string, { recursive: true, force: true });
  }
});

describe('legitimate multipart uploads', () => {
  it('stores a file in a directory inside the root', async () => {
    const res = await upload('photos');
    expect(res.statusCode).toBe(200);
    expect(putKeys()).toEqual(['media/photos/a.png']);
    expect(res.body.filename).toBe('a.png');
  });

  it('accepts leading and trailing slashes on the directory', async () => {
    const res = await upload('/photos/');
    expect(res.statusCode).toBe(200);
    expect(putKeys()).toEqual(['media/photos/a.png']);
  });

  it('accepts a filename containing a literal percent sign', async () => {
    const res = await upload('photos', '100%off.png');
    expect(res.statusCode).toBe(200);
    expect(putKeys()).toEqual(['media/photos/100%off.png']);
  });
});

describe('legitimate delete and listing', () => {
  it('deletes the identifier the listing returned', async () => {
    const res = await request('DELETE', {
      media: ['media', 'media/photos/a.png'],
    });
    expect(res.statusCode).toBe(200);
    expect(deletedKeys()).toEqual(['media/photos/a.png']);
  });

  it('deletes a key split across route segments', async () => {
    const res = await request('DELETE', {
      media: ['media', 'photos', 'a.png'],
    });
    expect(res.statusCode).toBe(200);
    expect(deletedKeys()).toHaveLength(1);
    expect(deletedKeys()[0].endsWith('photos/a.png')).toBe(true);
  });

  it('lists the root of the media area', async () => {
    const res = await request('GET', {});
    expect(res.statusCode).toBe(200);
    expect(prefixes()).toEqual(['media/']);
  });

  it('lists a directory inside the root', async () => {
    const res = await request('GET', { directory: 'photos' });
    expect(res.statusCode).toBe(200);
    expect(prefixes()).toEqual(['media/photos/']);
  });
});
