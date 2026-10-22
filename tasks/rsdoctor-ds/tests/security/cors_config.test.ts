import { afterEach, describe, expect, it } from '@rstest/core';
import { disposeSdk, startSdk, tryHttp, type Started } from '../support/helpers';

describe('the origin rule holds whatever the cross-origin configuration says', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  function readAs(origin: string) {
    return tryHttp({
      port: started!.port,
      path: '/api/manifest.json',
      method: 'GET',
      headers: { Origin: origin },
    });
  }

  it('refuses a non-local origin when cross-origin access is turned off', async () => {
    started = await startSdk({ server: { cors: false } });
    const outcome = await readAs('https://attacker.example');

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('enableRoutes');
    expect(res.headers['access-control-allow-origin']).not.toBe('*');
  });

  it('refuses a non-local origin when cross-origin access is turned on', async () => {
    started = await startSdk({ server: { cors: true } });
    const outcome = await readAs('https://attacker.example');

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('enableRoutes');
    expect(res.headers['access-control-allow-origin']).not.toBe('*');
  });

  it('refuses an origin the configuration does not name', async () => {
    started = await startSdk({
      server: { cors: { origin: 'https://partner.example' } },
    });
    const outcome = await readAs('https://attacker.example');

    expect(outcome.error).toBeUndefined();
    const res = outcome.result!;
    expect(res.status >= 400 && res.status < 500).toBe(true);
    expect(res.body).not.toContain('enableRoutes');
  });

  it('refuses a write from a non-local origin when cross-origin access is turned off', async () => {
    started = await startSdk({ server: { cors: false } });
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
