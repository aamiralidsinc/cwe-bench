import { afterEach, describe, expect, it } from '@rstest/core';
import { startAnalysisBridge } from '/workspace/packages/ai/dist/index.js';
import {
  disposeSdk,
  freePort,
  lanIPv4,
  startSdk,
  tryHttp,
  type Started,
} from '../support/helpers';

describe('the assistant bridge follows the same access rules', () => {
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

  function bridgeRequest(
    port: number,
    headers: Record<string, string> = {},
    hostname = '127.0.0.1',
  ) {
    return tryHttp({
      hostname,
      port,
      path: '/api/analysis',
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ api: '/api/routes', body: {} }),
    });
  }

  it('does not answer a non-local origin', async () => {
    started = await startSdk();
    bridge = await startAnalysisBridge({
      port: await freePort(),
      reportUrl: `http://127.0.0.1:${started.port}`,
    });
    const outcome = await bridgeRequest(bridge.port, {
      Origin: 'https://attacker.example',
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('Overall');
  });

  it('does not answer a request addressed to a foreign host', async () => {
    started = await startSdk();
    bridge = await startAnalysisBridge({
      port: await freePort(),
      reportUrl: `http://127.0.0.1:${started.port}`,
    });
    const outcome = await bridgeRequest(bridge.port, {
      Host: `attacker.example:${bridge.port}`,
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('Overall');
  });

  it('is not reachable through the machine address', async () => {
    const lan = lanIPv4();
    if (!lan) {
      return;
    }
    started = await startSdk();
    bridge = await startAnalysisBridge({
      port: await freePort(),
      reportUrl: `http://127.0.0.1:${started.port}`,
    });
    const outcome = await bridgeRequest(bridge.port, {}, lan);

    expect(outcome.result).toBeUndefined();
    expect(outcome.error).toBeDefined();
  });
});
