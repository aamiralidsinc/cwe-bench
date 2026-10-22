// The copy / move route shipped next to the DOS media handler. Both the source
// and destination object keys are caller-chosen and must stay inside the
// configured media root.
import { beforeEach, describe, it } from 'vitest';
import { createCopyHandler } from '@app/packages/next-tinacms-dos/src/copy-handler';
import {
  resetStubs,
  makeRes,
  pagesReq,
  sentInputs,
  expectRefused,
  expectConfined,
} from '../support/harness';

const ROOT = 'media';
const BUCKET = 'private-space';

function handler() {
  return createCopyHandler({
    config: {
      region: 'us-east-1',
      endpoint: 'https://sfo2.digitaloceanspaces.com',
    },
    bucket: BUCKET,
    mediaRoot: ROOT,
    authorized: async () => true,
  } as any);
}

function copyKeys(): string[] {
  const keys: string[] = [];
  for (const input of sentInputs('CopyObject')) {
    const source = String(input.CopySource || '');
    keys.push(source.startsWith(`${BUCKET}/`) ? source.slice(BUCKET.length + 1) : source);
    keys.push(String(input.Key));
  }
  return keys;
}

async function copy(from: string, to: string) {
  const res = makeRes();
  await handler()(pagesReq('POST', { from, to }), res);
  return res;
}

beforeEach(resetStubs);

describe('copy source and destination are confined to the media root', () => {
  it('refuses a source that walks above the root', async () => {
    const res = await copy('../secrets.png', 'media/archive/x.png');
    expectRefused(res, copyKeys());
  });

  it('refuses a destination that walks above the root', async () => {
    const res = await copy('media/photos/a.png', '../outside.png');
    expectRefused(res, copyKeys());
  });

  it('refuses an absolute source', async () => {
    const res = await copy('/etc/passwd', 'media/archive/x');
    expectRefused(res, copyKeys());
  });

  it('refuses an inner climb in the destination', async () => {
    const res = await copy('media/photos/a.png', 'a/../../../outside.png');
    expectRefused(res, copyKeys());
  });

  it('never copies a bucket key outside the root', async () => {
    const res = await copy('private/config.json', 'media/archive/x.json');
    expectConfined(res, copyKeys(), ROOT);
  });

  it('never copies to a bucket key outside the root', async () => {
    const res = await copy('media/photos/a.png', 'private/archive/x.png');
    expectConfined(res, copyKeys(), ROOT);
  });
});
