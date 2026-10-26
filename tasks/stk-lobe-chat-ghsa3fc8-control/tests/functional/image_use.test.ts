import { afterEach, describe, expect, it, vi } from 'vitest';

import { POST as imageUpload } from '@/app/api/files/image/route';

import { emulateNetwork, PUBLIC_URL, RecordedFetch } from '../support/harness';

// A correct fix may route its outbound call through a different HTTP client; the emulated network
// below covers either layer, so the legitimate-use checks do not depend on one implementation.
vi.mock('node-fetch', () => ({
  default: (input: any, init?: any) => (globalThis.fetch as any)(input, init),
}));


let network: RecordedFetch | undefined;

afterEach(() => {
  network?.restore();
  network = undefined;
});

describe('the image path still handles public pictures', () => {
  it('fetches a public picture and re-hosts it as before', async () => {
    network = emulateNetwork({
      [PUBLIC_URL]: () =>
        new Response(new Blob(['picture-bytes'], { type: 'image/png' }), {
          headers: { 'content-type': 'image/png' },
          status: 200,
        }),
      'https://api.imgur.com/3/upload': () =>
        new Response(JSON.stringify({ data: { link: 'https://i.imgur.com/hosted.png' }, success: true }), {
          headers: { 'content-type': 'application/json' },
          status: 200,
        }),
    });

    const response = await imageUpload(
      new Request('https://app.invalid/api/files/image', {
        body: JSON.stringify({ url: PUBLIC_URL }),
        method: 'POST',
      }),
    );

    expect(await response.json()).toEqual({ url: 'https://i.imgur.com/hosted.png' });
    expect(network.calls.map((entry) => entry.url)).toContain(PUBLIC_URL);
    expect(network.calls.map((entry) => entry.url)).toContain('https://api.imgur.com/3/upload');
  });
});