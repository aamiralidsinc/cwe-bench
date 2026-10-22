import { afterEach, describe, expect, it } from '@rstest/core';
import {
  disposeSdk,
  rawHttpRequest,
  startSdk,
  statusOf,
  tryHttp,
  type Started,
} from '../support/helpers';

describe('report server serves only requests addressed to a local host', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('refuses a request that names a foreign host', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/env',
      method: 'GET',
      headers: { Host: `attacker.example:${started.port}` },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain(String(started.port));
  });

  it('refuses a request that carries no host at all', async () => {
    started = await startSdk();
    const raw = await rawHttpRequest(
      started.port,
      'GET /api/env HTTP/1.0\r\n\r\n',
    );
    const status = statusOf(raw);

    expect(status).toBeGreaterThan(0);
    expect(status >= 400 && status < 500).toBe(true);
  });

  it('refuses a localhost origin whose name does not match the host', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/env',
      method: 'GET',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://other.localhost:${started.port}`,
      },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
  });
});
