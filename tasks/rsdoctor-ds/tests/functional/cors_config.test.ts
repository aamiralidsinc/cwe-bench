import { afterEach, describe, expect, it } from '@rstest/core';
import { disposeSdk, httpRequest, startSdk, type Started } from '../support/helpers';

describe('every cross-origin configuration keeps serving local clients', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('serves a client with no origin when cross-origin access is turned off', async () => {
    started = await startSdk({ server: { cors: false } });
    const res = await httpRequest({ port: started.port, path: '/api/env' });

    expect(res.status).toBe(200);
    expect(JSON.parse(res.body).port).toBe(started.port);
  });

  it('serves a local origin when cross-origin access is turned off', async () => {
    started = await startSdk({ server: { cors: false } });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://127.0.0.1:${started.port}`,
      },
    });

    expect(res.status).toBe(200);
  });

  it('serves a local origin when cross-origin access is turned on', async () => {
    started = await startSdk({ server: { cors: true } });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://127.0.0.1:${started.port}`,
      },
    });

    expect(res.status).toBe(200);
    expect(res.headers['access-control-allow-origin']).toBeDefined();
  });

  it('serves a local origin when a named origin is configured', async () => {
    started = await startSdk({
      server: { cors: { origin: 'https://partner.example' } },
    });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://127.0.0.1:${started.port}`,
      },
    });

    expect(res.status).toBe(200);
    expect(JSON.parse(res.body).port).toBe(started.port);
  });

  it('allows an origin named by a configured list', async () => {
    started = await startSdk({
      server: {
        cors: { origin: ['https://first.example', 'https://second.example'] },
      },
    });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      method: 'OPTIONS',
      headers: {
        Origin: 'https://second.example',
        'Access-Control-Request-Method': 'GET',
      },
    });

    expect(res.status).toBe(204);
    expect(res.headers['access-control-allow-origin']).toBe(
      'https://second.example',
    );
  });

  it('allows an origin matched by a configured pattern', async () => {
    started = await startSdk({
      server: { cors: { origin: /^https:\/\/[a-z]+\.partner\.example$/ } },
    });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      method: 'OPTIONS',
      headers: {
        Origin: 'https://app.partner.example',
        'Access-Control-Request-Method': 'GET',
      },
    });

    expect(res.status).toBe(204);
    expect(res.headers['access-control-allow-origin']).toBe(
      'https://app.partner.example',
    );
  });
});
