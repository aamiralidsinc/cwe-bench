// A legitimate upload with a normal file id must succeed and be downloadable
// again with identical bytes. Protects the path-traversal fix from rejecting
// valid file ids and the access-control fix from blocking the owner.
import { beforeEach, describe, expect, it } from 'vitest';

import { handlers as sync } from '@ss/app-sync.ts';
import { addAuth, addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

describe('legitimate upload/download round-trip', () => {
  let token;

  beforeEach(() => {
    clearAll();
    addAuth({ method: 'openid', active: 1, displayName: 'OpenID' });
    const uid = addUser({ userName: 'saver', role: 'BASIC' });
    token = addSession({ token: `tok-${uuidv4()}`, userId: uid });
  });

  it('uploads a new file and downloads the same content', async () => {
    const fileId = uuidv4();
    const payload = Buffer.from('a perfectly ordinary encrypted budget blob');

    const up = await request(sync)
      .post('/upload-user-file')
      .set('x-actual-token', token)
      .set('x-actual-name', 'my budget')
      .set('x-actual-file-id', fileId)
      .set('x-actual-format', '2')
      .set('Content-Type', 'application/encrypted-file')
      .send(payload);
    expect(up.status).toBe(200);
    expect(up.body?.status).toBe('ok');

    const down = await request(sync)
      .get('/download-user-file')
      .set('x-actual-token', token)
      .set('x-actual-file-id', fileId)
      .buffer(true)
      .parse((res, cb) => {
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => cb(null, Buffer.concat(chunks)));
      });
    expect(down.status).toBe(200);
    expect(Buffer.from(down.body).equals(payload)).toBe(true);
  });
});
