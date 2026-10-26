import { afterEach, describe, expect, it, vi } from 'vitest';

import { POST as gateway } from '@/app/api/plugin/gateway/route';

import { clientToken, emulateNetwork, RecordedFetch } from '../support/harness';

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

const PUBLIC_API = 'http://8.8.8.8/plugin/api';

const manifest = {
  api: [
    {
      description: 'answer',
      name: 'answer',
      parameters: { properties: {}, type: 'object' },
      url: PUBLIC_API,
    },
  ],
  identifier: 'public-plugin',
  meta: { avatar: 'icon', description: 'public plugin', title: 'Public plugin' },
  systemRole: 'you are a plugin',
  type: 'default',
  version: '1',
};

describe('plugin calls to public destinations still work', () => {
  it('calls a plugin api hosted at a public destination and returns its answer', async () => {
    network = emulateNetwork({
      [PUBLIC_API]: () =>
        new Response('plugin-answer', {
          headers: { 'content-type': 'text/plain' },
          status: 200,
        }),
    });

    const response = await gateway(
      new Request('https://app.invalid/api/plugin/gateway', {
        body: JSON.stringify({
          apiName: 'answer',
          arguments: '{}',
          identifier: 'public-plugin',
          manifest,
        }),
        headers: {
          'content-type': 'application/json',
          'X-lobe-chat-auth': clientToken({ accessCode: '' }),
        },
        method: 'POST',
      }),
    );

    expect(await response.text()).toBe('plugin-answer');
    expect(network.calls.map((entry) => entry.url)).toEqual([PUBLIC_API]);
  });
});