import { afterEach, describe, expect, it } from 'vitest';

import { POST as imageUpload } from '@/app/api/files/image/route';

import { Canary, isClientError, startCanary } from '../support/harness';

let canaries: Canary[] = [];

afterEach(async () => {
  for (const canary of canaries) await canary.close();
  canaries = [];
});

const canary = async () => {
  const started = await startCanary({ body: 'collected-image-bytes', contentType: 'image/png' });
  canaries.push(started);
  return started;
};

const call = (url: string) =>
  imageUpload(
    new Request('https://app.invalid/api/files/image', {
      body: JSON.stringify({ url }),
      method: 'POST',
    }),
  );

describe('a destination handed to the image path', () => {
  it('does not connect to a loopback address', async () => {
    const internal = await canary();

    const response = await call(`http://127.0.0.1:${internal.port}/internal/picture.png`);

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });

  it('does not connect to a loopback address written as a host name', async () => {
    const internal = await canary();

    const response = await call(`http://localhost:${internal.port}/internal/picture.png`);

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });
});
