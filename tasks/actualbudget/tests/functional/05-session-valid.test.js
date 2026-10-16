// An enabled user with a valid token must keep full access. Protects the
// session-expiration fix from rejecting legitimate, still-enabled sessions.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as account } from '@ss/app-account.js';
import { handlers as sync } from '@ss/app-sync.ts';
import { addAuth, addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

describe('enabled user session', () => {
  let token;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const uid = addUser({ userName: 'active-member', role: 'BASIC', enabled: 1 });
    token = addSession({ token: `tok-${uuidv4()}`, userId: uid, expiresAt: -1 });
  });

  it('validates an enabled user', async () => {
    const res = await request(account).get('/validate').set('x-actual-token', token);
    expect(res.status).toBe(200);
    expect(res.body?.data?.validated).toBe(true);
  });

  it('lets an enabled user list their files', async () => {
    const res = await request(sync).get('/list-user-files').set('x-actual-token', token);
    expect(res.status).toBe(200);
    expect(res.body?.status).toBe('ok');
  });
});
