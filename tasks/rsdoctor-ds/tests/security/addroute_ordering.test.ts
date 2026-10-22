import { afterEach, describe, expect, it } from '@rstest/core';
import { disposeSdk, startSdk, tryHttp, type Started } from '../support/helpers';

describe('custom registered routes follow the server access rules', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  async function startWithRoute() {
    started = await startSdk();
    started.sdk.server.addRoute('/api/custom/status', 'GET', () => ({
      marker: 'route-visible',
      root: '/workspace',
    }));
    return started;
  }

  it('does not answer a non-local origin', async () => {
    const target = await startWithRoute();
    const outcome = await tryHttp({
      port: target.port,
      path: '/api/custom/status',
      method: 'GET',
      headers: { Origin: 'https://attacker.example' },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('route-visible');
  });

  it('does not answer a request addressed to a foreign host', async () => {
    const target = await startWithRoute();
    const outcome = await tryHttp({
      port: target.port,
      path: '/api/custom/status',
      method: 'GET',
      headers: { Host: `attacker.example:${target.port}` },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('route-visible');
  });
});
