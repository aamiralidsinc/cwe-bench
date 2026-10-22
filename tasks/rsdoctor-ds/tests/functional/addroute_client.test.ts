import { afterEach, describe, expect, it } from '@rstest/core';
import { disposeSdk, startSdk, tryHttp, type Started } from '../support/helpers';

describe('routes registered on the report server serve local clients', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('answers a local request with no origin', async () => {
    started = await startSdk();
    started.sdk.server.addRoute('/api/custom/status', 'GET', () => ({
      marker: 'route-visible',
    }));

    const outcome = await tryHttp({
      port: started.port,
      path: '/api/custom/status',
    });
    expect(outcome.result?.status).toBe(200);
    expect(outcome.result?.body).toContain('route-visible');
  });

  it('answers a request from a local origin', async () => {
    started = await startSdk();
    started.sdk.server.addRoute('/api/custom/status', 'GET', () => ({
      marker: 'route-visible',
    }));

    const outcome = await tryHttp({
      port: started.port,
      path: '/api/custom/status',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://127.0.0.1:${started.port}`,
      },
    });
    expect(outcome.result?.status).toBe(200);
    expect(outcome.result?.body).toContain('route-visible');
  });
});
