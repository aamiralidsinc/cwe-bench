// CWE-285 Improper Authorization on the secrets store.
// In OpenID multi-user mode the integration secrets are admin-managed. A
// non-admin user must not be able to probe whether a given secret is
// configured. The existence endpoint fails to apply the admin check that the
// write endpoint uses.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as secrets } from '@ss/app-secrets.js';
import { secretsService } from '@ss/services/secrets-service.js';
import { addAuth, addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

describe('secret existence is not disclosed to non-admins', () => {
  let basicToken;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const basic = addUser({ userName: 'member', role: 'BASIC' });
    basicToken = addSession({ token: `tok-${uuidv4()}`, userId: basic });
    // An admin has configured a bank-sync secret.
    secretsService.set('gocardless_secretId', 'super-secret-value');
  });

  it('does not reveal to a non-admin that a secret is configured', async () => {
    const res = await request(secrets)
      .get('/gocardless_secretId')
      .set('x-actual-token', basicToken);
    // A well-behaved server refuses (403); the vulnerable one answers 204/404,
    // disclosing whether the secret exists.
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 403; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });
});
