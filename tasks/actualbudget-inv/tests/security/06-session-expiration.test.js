// CWE-613 Insufficient Session Expiration.
// When an admin disables a user, that user's previously issued session tokens
// must stop working. The session validation only checks that the token exists
// and has not timed out; it never rechecks whether the user is still enabled,
// so a disabled user keeps full access with an old token.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as account } from '@ss/app-account.js';
import { handlers as sync } from '@ss/app-sync.ts';
import { addAuth, addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

describe("a disabled user's existing token is rejected", () => {
  let token;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    // The user was disabled by an admin but still holds a valid, unexpired token.
    const uid = addUser({ userName: 'revoked', role: 'BASIC', enabled: 0 });
    token = addSession({ token: `tok-${uuidv4()}`, userId: uid, expiresAt: -1 });
  });

  it('rejects the disabled user on /account/validate', async () => {
    const res = await request(account).get('/validate').set('x-actual-token', token);
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 401; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });

  it('rejects the disabled user on a sync data endpoint', async () => {
    const res = await request(sync).get('/list-user-files').set('x-actual-token', token);
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 401; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });
});
