// Authorized file access must keep working: the owner, a user who was granted
// access, and a server admin can all reach a file; the owner can rename it.
// Protects the access-control fix from over-blocking legitimate users.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as sync } from '@ss/app-sync.ts';
import {
  addAuth,
  addFile,
  addSession,
  addUser,
  clearAll,
  grantAccess,
  request,
  uuidv4,
} from '../lib/harness.js';

describe('authorized sync file access', () => {
  let ownerToken;
  let sharedToken;
  let adminToken;
  let fileId;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const owner = addUser({ userName: 'owner', role: 'BASIC' });
    const shared = addUser({ userName: 'collaborator', role: 'BASIC' });
    const admin = addUser({ userName: 'root', role: 'ADMIN' });
    ownerToken = addSession({ token: `tok-${uuidv4()}`, userId: owner });
    sharedToken = addSession({ token: `tok-${uuidv4()}`, userId: shared });
    adminToken = addSession({ token: `tok-${uuidv4()}`, userId: admin });
    fileId = addFile({ id: `file-${uuidv4()}`, name: 'the budget', owner });
    grantAccess(shared, fileId);
  });

  it('lets the owner read their file info', async () => {
    const res = await request(sync)
      .get('/get-user-file-info')
      .set('x-actual-token', ownerToken)
      .set('x-actual-file-id', fileId);
    expect(res.status).toBe(200);
    expect(res.body?.data?.fileId).toBe(fileId);
  });

  it('lets a granted collaborator read the file info', async () => {
    const res = await request(sync)
      .get('/get-user-file-info')
      .set('x-actual-token', sharedToken)
      .set('x-actual-file-id', fileId);
    expect(res.status).toBe(200);
  });

  it('lets a server admin read the file info', async () => {
    const res = await request(sync)
      .get('/get-user-file-info')
      .set('x-actual-token', adminToken)
      .set('x-actual-file-id', fileId);
    expect(res.status).toBe(200);
  });

  it('lets the owner rename their own file', async () => {
    const res = await request(sync)
      .post('/update-user-filename')
      .set('x-actual-token', ownerToken)
      .send({ fileId, name: 'renamed budget' });
    expect(res.status).toBe(200);
    expect(res.body?.status).toBe('ok');
  });
});
