// CWE-284 / CWE-862 Privilege escalation on a server migrated from password
// auth to OpenID. A normal (BASIC) user must not be able to take over the
// built-in owner/admin account. The attack: overwrite the server password via
// an endpoint that fails to check authorization, then log in with the forced
// "password" method to receive the anonymous owner's ADMIN token.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as account } from '@ss/app-account.js';
import {
  addAuth,
  addPasswordAuth,
  addSession,
  addUser,
  clearAll,
  request,
  uuidv4,
} from '../lib/harness.js';

describe('a basic user cannot escalate to admin', () => {
  let attackerToken;

  beforeEach(() => {
    clearAll();
    // Server was bootstrapped with a password (the anonymous owner/admin), then
    // migrated to OpenID: the password row is left behind (inactive), OpenID is
    // the active method.
    addUser({ userName: '', role: 'ADMIN', owner: 1, enabled: 1 });
    addPasswordAuth('original-owner-password', { active: 0 });
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const attacker = addUser({ userName: 'intruder', role: 'BASIC' });
    attackerToken = addSession({
      token: `tok-${uuidv4()}`,
      userId: attacker,
      authMethod: 'openid',
    });
  });

  it('cannot obtain an admin session by resetting the password and logging in', async () => {
    const forced = 'attacker-chosen-password';

    // Step 1: try to overwrite the server password as a non-admin.
    await request(account)
      .post('/change-password')
      .set('x-actual-token', attackerToken)
      .send({ password: forced });

    // Step 2: force the password login method and log in with the chosen value.
    const login = await request(account)
      .post('/login')
      .send({ loginMethod: 'password', password: forced });

    const escalatedToken = login.body?.data?.token;

    // If no token was issued, the escalation already failed.
    if (escalatedToken) {
      const validate = await request(account)
        .get('/validate')
        .set('x-actual-token', escalatedToken);
      // The attacker must not end up validated as an ADMIN.
      const permission = validate.body?.data?.permission;
      expect(permission).not.toBe('ADMIN');
    } else {
      expect(escalatedToken).toBeFalsy();
    }
  });
});
