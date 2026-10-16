// An authenticated user must still be able to reach the bank-sync status
// endpoints. Protects the missing-authentication fix from blocking legitimate,
// logged-in callers (the endpoints must gain a session check, not disappear).
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as simplefin } from '@ss/app-simplefin/app-simplefin.js';
import { handlers as pluggyai } from '@ss/app-pluggyai/app-pluggyai.js';
import { addAuth, addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

describe('authenticated bank-sync status', () => {
  let token;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const uid = addUser({ userName: 'member', role: 'BASIC' });
    token = addSession({ token: `tok-${uuidv4()}`, userId: uid });
  });

  it('returns SimpleFIN status for an authenticated user', async () => {
    const res = await request(simplefin).post('/status').set('x-actual-token', token).send({});
    expect(res.status).toBe(200);
    expect(res.body?.status).toBe('ok');
    expect(res.body?.data?.configured).toBe(false);
  });

  it('returns Pluggy.ai status for an authenticated user', async () => {
    const res = await request(pluggyai).post('/status').set('x-actual-token', token).send({});
    expect(res.status).toBe(200);
    expect(res.body?.status).toBe('ok');
    expect(res.body?.data?.configured).toBe(false);
  });
});
