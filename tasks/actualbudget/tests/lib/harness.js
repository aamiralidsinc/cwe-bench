// Shared helpers for the CWE verifier tests. These tests drive the Actual sync
// server's Express handlers over HTTP (via supertest) against the real on-disk
// SQLite account database, exactly as the server's own test-suite does. The
// code under test is the solver's source under /app (imported through the
// "@ss" alias configured in the vitest configs); only this harness and the
// test files themselves live under /tests and are never read from /app.
import * as bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';

import { getAccountDb } from '@ss/account-db.js';

export { default as request } from 'supertest';
export { uuidv4 };

export function db() {
  return getAccountDb();
}

// Wipe every table we touch so each test starts from a known, isolated state.
export function clearAll() {
  const d = getAccountDb();
  for (const sql of [
    'DELETE FROM sessions',
    'DELETE FROM user_access',
    'DELETE FROM files',
    'DELETE FROM users',
    'DELETE FROM auth',
    'DELETE FROM secrets',
    'DELETE FROM server_prefs',
  ]) {
    try {
      d.mutate(sql);
    } catch {
      // table may not exist in some schema states; ignore
    }
  }
}

export function addAuth({ method, active = 0, extraData = null, displayName = method }) {
  getAccountDb().mutate(
    'INSERT INTO auth (method, display_name, extra_data, active) VALUES (?, ?, ?, ?)',
    [method, displayName, extraData, active ? 1 : 0],
  );
}

// Create a password auth row whose stored hash is bcrypt(password).
export function addPasswordAuth(password, { active = 0 } = {}) {
  addAuth({
    method: 'password',
    active,
    displayName: 'Password',
    extraData: bcrypt.hashSync(password, 12),
  });
}

export function addUser({ id = uuidv4(), userName, role = 'BASIC', owner = 0, enabled = 1 }) {
  getAccountDb().mutate(
    'INSERT INTO users (id, user_name, display_name, enabled, owner, role) VALUES (?, ?, ?, ?, ?, ?)',
    [id, userName, userName, enabled ? 1 : 0, owner ? 1 : 0, role],
  );
  return id;
}

export function addSession({ token, userId, authMethod = 'openid', expiresAt = -1 }) {
  getAccountDb().mutate(
    'INSERT INTO sessions (token, expires_at, user_id, auth_method) VALUES (?, ?, ?, ?)',
    [token, expiresAt, userId, authMethod],
  );
  return token;
}

// Insert a file row owned by ownerId (as app-sync's FilesService.set would).
export function addFile({ id, name = null, owner, groupId = null }) {
  getAccountDb().mutate(
    'INSERT INTO files (id, group_id, sync_version, name, deleted, owner) VALUES (?, ?, ?, ?, 0, ?)',
    [id, groupId, '2', name, owner],
  );
  return id;
}

export function grantAccess(userId, fileId) {
  getAccountDb().mutate(
    'INSERT INTO user_access (user_id, file_id) VALUES (?, ?)',
    [userId, fileId],
  );
}

export function bcryptHash(password) {
  return bcrypt.hashSync(password, 12);
}
