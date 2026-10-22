import { afterEach, describe, expect, it } from '@rstest/core';
import { disposeSdk, startSdk, tryHttp, type Started } from '../support/helpers';

describe('report server refuses cross-origin browser reads', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('does not serve analysis data to a non-local origin', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/manifest.json',
      method: 'GET',
      headers: { Origin: 'https://attacker.example' },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('/workspace');
    expect(res.body).not.toContain('enableRoutes');
    expect(res.headers['access-control-allow-origin']).not.toBe('*');
  });

  it('does not serve a write API result to a non-local origin', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/routes',
      method: 'POST',
      headers: {
        Origin: 'https://attacker.example',
        'Content-Type': 'application/json',
      },
      body: '{}',
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('Overall');
  });

  it('does not grant a preflight request from a non-local origin', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/manifest.json',
      method: 'OPTIONS',
      headers: {
        Origin: 'https://attacker.example',
        'Access-Control-Request-Method': 'GET',
      },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    const granted = res.headers['access-control-allow-origin'];
    expect(granted).not.toBe('*');
    expect(granted).not.toBe('https://attacker.example');
  });

  it('does not serve the report page to a non-local origin', async () => {
    started = await startSdk();
    const outcome = await tryHttp({
      port: started.port,
      path: '/index.html',
      method: 'GET',
      headers: { Origin: 'https://attacker.example' },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('<html');
  });

  it('does not grant a cross-origin read when CORS is turned off', async () => {
    started = await startSdk({ server: { cors: false } });
    const outcome = await tryHttp({
      port: started.port,
      path: '/api/env',
      method: 'GET',
      headers: { Origin: 'https://attacker.example' },
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    const granted = res.headers['access-control-allow-origin'];
    expect(granted).not.toBe('*');
    expect(granted).not.toBe('https://attacker.example');
  });

  it('refuses a write request from another origin without side effects', async () => {
    started = await startSdk();
    let touched: number | undefined;
    started.sdk.applyErrorFix = async (id: number) => {
      touched = id;
    };

    const outcome = await tryHttp({
      port: started.port,
      path: '/api/apply/error/fix',
      method: 'POST',
      headers: {
        Origin: 'https://attacker.example',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id: 7 }),
    });

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(touched).toBeUndefined();
  });
});
