// The presigned-upload route on the primary S3 media handler. A caller picks
// the object key; it must resolve inside the configured media root whatever
// shape it arrives in.
import { beforeEach, describe, it } from 'vitest';
import { createMediaHandler } from '@app/packages/next-tinacms-s3/src/handlers';
import {
  resetStubs,
  makeRes,
  pagesReq,
  presignedKeys,
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

async function requestUploadUrl(query: Record<string, any>) {
  const res = makeRes();
  await handler()(pagesReq('GET', query), res);
  return res;
}

beforeEach(resetStubs);

describe('presigned upload url is confined to the media root', () => {
  it('refuses an absolute object key', async () => {
    const res = await requestUploadUrl({ key: '/etc/passwd' });
    expectRefused(res, presignedKeys());
  });

  it('refuses a relative key that walks above the root', async () => {
    const res = await requestUploadUrl({ key: '../secrets.png' });
    expectRefused(res, presignedKeys());
  });

  it('refuses an inner climb that leaves the root', async () => {
    const res = await requestUploadUrl({ key: 'photos/../../outside.png' });
    expectRefused(res, presignedKeys());
  });

  it('refuses a windows-style separator', async () => {
    const res = await requestUploadUrl({ key: '..\\outside.png' });
    expectRefused(res, presignedKeys());
  });

  it('refuses an absolute windows drive key', async () => {
    const res = await requestUploadUrl({ key: 'C:/Windows/system.ini' });
    expectRefused(res, presignedKeys());
  });

  it('refuses an invalid key when the query value is a list', async () => {
    const res = await requestUploadUrl({ key: ['../outside.png', 'ok.png'] });
    expectRefused(res, presignedKeys());
  });

  it('never mints a url for a bucket key outside the root', async () => {
    const res = await requestUploadUrl({ key: 'private/config.json' });
    expectConfined(res, presignedKeys(), ROOT);
  });
});
