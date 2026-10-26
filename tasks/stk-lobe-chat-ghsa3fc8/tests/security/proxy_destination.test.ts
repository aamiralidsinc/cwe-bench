import { afterEach, describe, expect, it } from 'vitest';

import { POST as fetchService } from '@/app/api/proxy/route';

import { Canary, isClientError, startCanary } from '../support/harness';

let canaries: Canary[] = [];

afterEach(async () => {
  for (const canary of canaries) await canary.close();
  canaries = [];
});

const canary = async (host?: string) => {
  const started = await startCanary({ host });
  canaries.push(started);
  return started;
};

const call = (destination: string) =>
  fetchService(new Request('https://app.invalid/api/proxy', { body: destination, method: 'POST' }));

describe('a destination handed to the general-purpose fetch service', () => {
  it('does not connect to a loopback address', async () => {
    const internal = await canary();

    const response = await call(`http://127.0.0.1:${internal.port}/internal/state`);

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });

  it('does not connect to a loopback address written as a host name', async () => {
    const internal = await canary();

    const response = await call(`http://localhost:${internal.port}/internal/state`);

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });

  it('does not connect to an IPv6 loopback address', async () => {
    const internal = await canary('::1');

    const response = await call(`http://[::1]:${internal.port}/internal/state`);

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });

  it('does not connect to any other address in the loopback range', async () => {
    const internal = await canary('0.0.0.0');

    const response = await call(`http://127.0.0.2:${internal.port}/internal/state`);

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });
});
