import { afterEach, describe, expect, it, vi } from 'vitest';

import { POST as fetchService } from '@/app/api/proxy/route';

import { emulateNetwork, PUBLIC_URL, PUBLIC_URL_2, RecordedFetch } from '../support/harness';

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

const call = (destination: string) =>
  fetchService(new Request('https://app.invalid/api/proxy', { body: destination, method: 'POST' }));

describe('the general-purpose fetch service still serves public destinations', () => {
  it('returns what a public destination answers, with its headers', async () => {
    network = emulateNetwork({
      [PUBLIC_URL]: () =>
        new Response('remote-plugin-manifest', {
          headers: { 'content-type': 'application/json', 'x-remote': 'yes' },
          status: 200,
        }),
    });

    const response = await call(PUBLIC_URL);

    expect(response.status).toBe(200);
    expect(await response.text()).toBe('remote-plugin-manifest');
    expect(response.headers.get('x-remote')).toBe('yes');
    expect(network.calls.map((entry) => entry.url)).toEqual([PUBLIC_URL]);
  });

  it('follows a redirect between public destinations', async () => {
    network = emulateNetwork({
      [PUBLIC_URL]: (init) =>
        init?.redirect === 'manual'
          ? new Response(null, { headers: { location: PUBLIC_URL_2 }, status: 302 })
          : new Response('final-body', { status: 200 }),
      [PUBLIC_URL_2]: () => new Response('final-body', { status: 200 }),
    });

    const response = await call(PUBLIC_URL);

    expect(await response.text()).toBe('final-body');
  });
});