// CWE-22 Path Traversal.
// The sync file-upload endpoint builds the on-disk path from the attacker-
// controlled x-actual-file-id header. A value containing traversal sequences
// must not be able to make the server write a file outside the configured user
// files directory.
import fs from 'node:fs';
import { join, resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { handlers as sync } from '@ss/app-sync.ts';
import { config } from '@ss/load-config.js';
import { addSession, addUser, clearAll, request, uuidv4 } from '../lib/harness.js';

// Where the vulnerable upload handler writes a file id: the original formula of
// util/paths.js getPathForUserFile, computed here so the test never depends on
// product code the solver may change (a fix may make that helper throw).
function unsafePathForUserFile(fileId) {
  return join(resolve(config.get('userFiles')), `file-${fileId}.blob`);
}

describe('sync upload rejects path traversal in the file id', () => {
  let token;
  let marker;

  beforeEach(() => {
    clearAll();
    const uid = addUser({ userName: 'attacker', role: 'BASIC' });
    token = addSession({ token: `tok-${uuidv4()}`, userId: uid });
    marker = `cwe-traversal-${uuidv4()}`;
  });

  afterEach(() => {
    // Clean up anything the vulnerable code may have written outside userFiles.
    const escaped = unsafePathForUserFile(`../../../../../../../../tmp/${marker}`);
    try {
      fs.rmSync(escaped, { force: true });
    } catch {
      /* ignore */
    }
  });

  it('does not write outside the user-files directory', async () => {
    const fileId = `../../../../../../../../tmp/${marker}`;
    const escapedPath = unsafePathForUserFile(fileId);

    const res = await request(sync)
      .post('/upload-user-file')
      .set('x-actual-token', token)
      .set('x-actual-name', 'budget')
      .set('x-actual-file-id', fileId)
      .set('x-actual-format', '2')
      .set('Content-Type', 'application/encrypted-file')
      .send(Buffer.from('owned-by-attacker'));

    // The security property: nothing was written outside userFiles.
    expect(fs.existsSync(escapedPath)).toBe(false);
    // And a well-behaved server rejects the request rather than accepting it.
    expect(res.status).not.toBe(200);
  });
});
