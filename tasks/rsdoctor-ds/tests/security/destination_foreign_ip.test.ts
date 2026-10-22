import { afterEach, describe, expect, it } from '@rstest/core';
import { startAnalysisBridge } from '/workspace/packages/ai/dist/index.js';
import {
  disposeSdk,
  freePort,
  startSdk,
  tryHttp,
  type Started,
} from '../support/helpers';

describe('only a loopback address of this machine is a local destination', () => {
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

  it('refuses a request addressed to a non-loopback IPv4 address', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/manifest.json',
      method: 'GET',
      headers: { Host: `203.0.113.9:${started.port}` },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('enableRoutes');
  });

  it('refuses a request addressed to a non-loopback IPv6 address', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/manifest.json',
      method: 'GET',
      headers: { Host: `[2001:db8::1]:${started.port}` },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('enableRoutes');
  });

  it('the assistant bridge refuses a non-loopback destination', async () => {
    started = await startSdk();
    started.sdk.addClientRoutes(['Overall']);
    bridge = await startAnalysisBridge({
      port: await freePort(),
      reportUrl: `http://127.0.0.1:${started.port}`,
    });

    const outcome = await tryHttp({
      port: bridge.port,
      path: '/api/analysis',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Host: `203.0.113.9:${bridge.port}`,
      },
      body: JSON.stringify({ api: '/api/routes', body: {} }),
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('Overall');
  });
});
