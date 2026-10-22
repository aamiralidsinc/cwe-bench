import { afterEach, describe, expect, it } from '@rstest/core';
import { startAnalysisBridge } from '/workspace/packages/ai/dist/index.js';
import {
  disposeSdk,
  freePort,
  httpRequest,
  startSdk,
  type Started,
} from '../support/helpers';

describe('legitimate local addresses keep working', () => {
  let started: Started | undefined;
  let bridge: any;

  afterEach(async () => {
    if (bridge) {
      await bridge.close();
      bridge = undefined;
    }
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('serves a request addressed to another loopback address', async () => {
    started = await startSdk();
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      headers: { Host: `127.0.0.2:${started.port}` },
    });

    expect(res.status).toBe(200);
    expect(JSON.parse(res.body).port).toBe(started.port);
  });

  it('serves a page on another loopback address', async () => {
    started = await startSdk();
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://127.0.0.2:${started.port}`,
      },
    });

    expect(res.status).toBe(200);
    expect(res.headers['access-control-allow-origin']).toBeDefined();
  });

  it('serves a page on the IPv6 loopback origin', async () => {
    started = await startSdk();
    const res = await httpRequest({
      port: started.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${started.port}`,
        Origin: `http://[::1]:${started.port}`,
      },
    });

    expect(res.status).toBe(200);
    expect(res.headers['access-control-allow-origin']).toBeDefined();
  });

  it('the assistant bridge serves a request addressed to localhost', async () => {
    started = await startSdk();
    bridge = await startAnalysisBridge({
      port: await freePort(),
      reportUrl: `http://127.0.0.1:${started.port}`,
    });

    const res = await httpRequest({
      port: bridge.port,
      path: '/health',
      headers: { Host: `localhost:${bridge.port}` },
    });

    expect(res.status).toBe(200);
  });
});
