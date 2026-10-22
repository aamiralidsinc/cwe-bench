import { afterEach, describe, expect, it } from '@rstest/core';
import { RsdoctorSDK } from '/workspace/packages/sdk/dist/index.js';
import { normalizeUserConfig } from '/workspace/packages/core/dist/inner-plugins/index.js';
import { RsdoctorRspackPlugin } from '/workspace/packages/rspack-plugin/dist/index.js';
import {
  disposeSdk,
  freePort,
  httpRequest,
  startSdk,
  tryHttp,
  type Started,
} from '../support/helpers';

describe('report server configuration keeps working', () => {
  let started: Started | undefined;
  let extra: any;

  afterEach(async () => {
    if (extra) {
      await disposeSdk(extra);
      extra = undefined;
    }
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('honours the configured server port', async () => {
    const port = await freePort();
    started = await startSdk({ port });
    expect(started.port).toBe(port);
    const res = await httpRequest({ port, path: '/api/env' });
    expect(res.status).toBe(200);
  });

  it('keeps the legacy port option working', async () => {
    const port = await freePort();
    extra = new RsdoctorSDK({ name: 'legacy-port', root: '/workspace', port });
    await extra.bootstrap();
    expect(extra.server.port).toBe(port);
    const res = await httpRequest({ port, path: '/api/env' });
    expect(res.status).toBe(200);
  });

  it('allows a configured custom origin', async () => {
    started = await startSdk({
      server: { cors: { origin: 'https://partner.example' } },
    });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      method: 'OPTIONS',
      headers: {
        Origin: 'https://partner.example',
        'Access-Control-Request-Method': 'GET',
      },
    });

    expect(res.status).toBe(204);
    expect(res.headers['access-control-allow-origin']).toBe(
      'https://partner.example',
    );
  });

  it('keeps local origins for a partial cors configuration', async () => {
    started = await startSdk({ server: { cors: { credentials: true } } });
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      method: 'OPTIONS',
      headers: {
        Origin: `http://127.0.0.1:${started.port}`,
        'Access-Control-Request-Method': 'GET',
      },
    });

    expect(res.status).toBe(204);
    expect(res.headers['access-control-allow-origin']).toBeDefined();
  });

  it('serves local clients when cors is disabled', async () => {
    started = await startSdk({ server: { cors: false } });
    const outcome = await tryHttp({ port: started.port, path: '/api/env' });
    expect(outcome.result?.status).toBe(200);
  });

  it('carries the server option through the config loader', () => {
    const normalized = normalizeUserConfig({
      server: { port: 4321, cors: false },
    } as never);
    expect(normalized.server.port).toBe(4321);
    expect(normalized.server.cors).toBe(false);
  });

  it('carries the server option through the bundler plugin', async () => {
    const port = await freePort();
    const plugin: any = new RsdoctorRspackPlugin({ server: { port } });
    expect(plugin.sdk.server.port).toBe(port);
  });
});
