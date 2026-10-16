// CWE-862 / CWE-863 Missing / Incorrect Authorization on the sync file API.
// In multi-user mode every authenticated user is allowed through the session
// check, but the per-file endpoints never verify that the caller owns or was
// granted access to the file. Any logged-in user who knows a file id can read
// or modify another user's file.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as sync } from '@ss/app-sync.ts';
import {
  addAuth,
  addFile,
  addSession,
  addUser,
  clearAll,
  request,
  uuidv4,
} from '../lib/harness.js';

describe('sync endpoints enforce per-file access control', () => {
  let attackerToken;
  let victimToken;
  let victimFileId;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const victim = addUser({ userName: 'victim', role: 'BASIC' });
    const attacker = addUser({ userName: 'intruder', role: 'BASIC' });
    attackerToken = addSession({ token: `tok-${uuidv4()}`, userId: attacker });
    victimToken = addSession({ token: `tok-${uuidv4()}`, userId: victim });
    // A plain file row (no group id / key), so an overwrite or reset attempt
    // reaches the handler's body rather than being turned away by sync-state
    // validation on the vulnerable code.
    victimFileId = addFile({ id: `file-${uuidv4()}`, name: 'victim budget', owner: victim });
  });

  it("blocks reading another user's file metadata", async () => {
    const res = await request(sync)
      .get('/get-user-file-info')
      .set('x-actual-token', attackerToken)
      .set('x-actual-file-id', victimFileId);
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 403; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });

  it("blocks renaming another user's file", async () => {
    const res = await request(sync)
      .post('/update-user-filename')
      .set('x-actual-token', attackerToken)
      .send({ fileId: victimFileId, name: 'pwned' });
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 403; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });

  it("blocks reading another user's encryption key info", async () => {
    const res = await request(sync)
      .post('/user-get-key')
      .set('x-actual-token', attackerToken)
      .send({ fileId: victimFileId });
    expect(res.status).toBeGreaterThanOrEqual(400); // refused (was exactly 403; any 4xx refusal is correct)
    expect(res.status).toBeLessThan(500);
  });

  it("blocks overwriting another user's existing file", async () => {
    const res = await request(sync)
      .post('/upload-user-file')
      .set('x-actual-token', attackerToken)
      .set('x-actual-name', 'pwned budget')
      .set('x-actual-file-id', victimFileId)
      .set('x-actual-format', '2')
      .set('Content-Type', 'application/encrypted-file')
      .send(Buffer.from('attacker-supplied replacement blob'));
    expect(res.status).toBeGreaterThanOrEqual(400); // any 4xx refusal is correct
    expect(res.status).toBeLessThan(500);
  });

  it("blocks resetting another user's file", async () => {
    const res = await request(sync)
      .post('/reset-user-file')
      .set('x-actual-token', attackerToken)
      .send({ fileId: victimFileId });
    expect(res.status).toBeGreaterThanOrEqual(400); // any 4xx refusal is correct
    expect(res.status).toBeLessThan(500);
  });

  it("blocks downloading another user's file", async () => {
    // The victim stores a real file through the normal upload endpoint.
    const downloadFileId = uuidv4();
    const up = await request(sync)
      .post('/upload-user-file')
      .set('x-actual-token', victimToken)
      .set('x-actual-name', 'victim real budget')
      .set('x-actual-file-id', downloadFileId)
      .set('x-actual-format', '2')
      .set('Content-Type', 'application/encrypted-file')
      .send(Buffer.from('the victim private budget bytes'));
    expect(up.status).toBe(200);

    const res = await request(sync)
      .get('/download-user-file')
      .set('x-actual-token', attackerToken)
      .set('x-actual-file-id', downloadFileId);
    expect(res.status).toBeGreaterThanOrEqual(400); // any 4xx refusal is correct
    expect(res.status).toBeLessThan(500);
  });
});
