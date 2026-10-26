import { afterEach, describe, expect, it } from 'vitest';

import { POST as gateway } from '@/app/api/plugin/gateway/route';

import { Canary, clientToken, isClientError, startCanary } from '../support/harness';

let canaries: Canary[] = [];

afterEach(async () => {
  for (const canary of canaries) await canary.close();
  canaries = [];
});

const canary = async () => {
  const started = await startCanary({ body: { plugins: [] } });
  canaries.push(started);
  return started;
};

const manifestWith = (url: string) => ({
  api: [
    {
      description: 'reveal',
      name: 'reveal',
      parameters: { properties: {}, type: 'object' },
      url,
    },
  ],
  identifier: 'any-plugin',
  meta: { avatar: 'icon', description: 'any plugin', title: 'Any plugin' },
  systemRole: 'you are a plugin',
  type: 'default',
  version: '1',
});

const call = (payload: Record<string, unknown>) =>
  gateway(
    new Request('https://app.invalid/api/plugin/gateway', {
      body: JSON.stringify({
        apiName: 'reveal',
        arguments: '{}',
        identifier: 'any-plugin',
        ...payload,
      }),
      headers: {
        'content-type': 'application/json',
        'X-lobe-chat-auth': clientToken({ accessCode: '' }),
      },
      method: 'POST',
    }),
  );

describe('a destination carried by a plugin call', () => {
  it('does not connect to a loopback address named by a plugin api', async () => {
    const internal = await canary();

    const response = await call({
      manifest: manifestWith(`http://127.0.0.1:${internal.port}/internal/api`),
    });

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });

  it('does not connect to a loopback address named as a plugin index', async () => {
    const internal = await canary();

    const response = await call({ indexUrl: `http://127.0.0.1:${internal.port}/internal/index.json` });

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });
});
