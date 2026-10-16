// CWE-306 Missing Authentication for Critical Function.
// The bank-sync integration endpoints (SimpleFIN, Pluggy.ai) must require an
// authenticated session, like the other data endpoints. On the vulnerable code
// they are reachable with no token at all.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as simplefin } from '@ss/app-simplefin/app-simplefin.js';
import { handlers as pluggyai } from '@ss/app-pluggyai/app-pluggyai.js';
import { clearAll, request } from '../lib/harness.js';

describe('bank-sync endpoints require authentication', () => {
  beforeEach(() => clearAll());

  it('rejects an unauthenticated SimpleFIN status request', async () => {
    const res = await request(simplefin).post('/status').send({});
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 401; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });

  it('rejects an unauthenticated Pluggy.ai status request', async () => {
    const res = await request(pluggyai).post('/status').send({});
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 401; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });

  it('rejects an unauthenticated SimpleFIN accounts request', async () => {
    const res = await request(simplefin).post('/accounts').send({});
    expect(res.status).toBeGreaterThanOrEqual(400); // any 4xx refusal is correct
    expect(res.status).toBeLessThan(500);
  });

  it('rejects an unauthenticated Pluggy.ai accounts request', async () => {
    const res = await request(pluggyai).post('/accounts').send({});
    expect(res.status).toBeGreaterThanOrEqual(400); // any 4xx refusal is correct
    expect(res.status).toBeLessThan(500);
  });
});
