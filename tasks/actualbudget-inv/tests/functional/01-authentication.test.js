// Legitimate authentication must keep working: a correct password logs in and
// the issued token validates; a wrong password is refused. Protects the auth/
// session hardening from breaking normal login.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as account } from '@ss/app-account.js';
import { addPasswordAuth, addUser, clearAll, request } from '../lib/harness.js';

describe('password login', () => {
  const PASSWORD = 'correct-horse-battery';

  beforeEach(() => {
    clearAll();
    // Single-user password server: the anonymous owner is the admin.
    addUser({ userName: '', role: 'ADMIN', owner: 1, enabled: 1 });
    addPasswordAuth(PASSWORD, { active: 1 });
  });

  it('issues a token for the correct password and validates it', async () => {
    const login = await request(account).post('/login').send({ password: PASSWORD });
    expect(login.status).toBe(200);
    const token = login.body?.data?.token;
    expect(token).toBeTruthy();

    const validate = await request(account).get('/validate').set('x-actual-token', token);
    expect(validate.status).toBe(200);
    expect(validate.body?.data?.validated).toBe(true);
    expect(validate.body?.data?.permission).toBe('ADMIN');
  });

  it('refuses an incorrect password', async () => {
    const login = await request(account).post('/login').send({ password: 'wrong' });
    expect(login.status).toBe(400);
    expect(login.body?.data?.token).toBeFalsy();
  });
});
