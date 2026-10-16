// In OpenID mode an admin must still be able to query the secrets store:
// a configured secret reports present (204), an unset one reports absent (404).
// Protects the secrets authorization fix from locking admins out.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as secrets } from '@ss/app-secrets.js';
import { secretsService } from '@ss/services/secrets-service.js';
import { addAuth, addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

describe('admin secret management in OpenID mode', () => {
  let adminToken;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const admin = addUser({ userName: 'root', role: 'ADMIN' });
    adminToken = addSession({ token: `tok-${uuidv4()}`, userId: admin });
    secretsService.set('gocardless_secretId', 'configured-value');
  });

  it('reports a configured secret as present for an admin', async () => {
    const res = await request(secrets)
      .get('/gocardless_secretId')
      .set('x-actual-token', adminToken);
    expect(res.status).toBe(204);
  });

  it('reports an unset secret as absent for an admin', async () => {
    const res = await request(secrets)
      .get('/simplefin_accessKey')
      .set('x-actual-token', adminToken);
    expect(res.status).toBe(404);
  });
});
