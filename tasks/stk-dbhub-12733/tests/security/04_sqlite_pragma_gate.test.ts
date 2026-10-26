import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { DatabaseSync } from 'node:sqlite';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { connectSources, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/sqlite/index.js';

let dir: string;
let file: string;

const source = () => ({
  id: 'default',
  type: 'sqlite' as const,
  dsn: 'sqlite://' + file,
  init_script: 'CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);',
});

function userVersion(): number {
  const db = new DatabaseSync(file, { readOnly: true });
  try {
    return Number((db.prepare('PRAGMA user_version').get() as { user_version: number }).user_version);
  } finally {
    db.close();
  }
}

describe('the read-only admission decision refuses pragma setters', () => {
  beforeAll(async () => {
    dir = mkdtempSync(path.join(tmpdir(), 'dbhub-pragma-'));
    file = path.join(dir, 'app.db');
    await connectSources([source()], true);
  });
  afterAll(() => {
    try {
      rmSync(dir, { recursive: true, force: true });
    } catch {
      /* best-effort */
    }
  });

  for (const sql of [
    'PRAGMA user_version = 1337',
    'PRAGMA user_version=1337',
    'PRAGMA user_version(1337)',
    'PRAGMA application_id = 1',
    'PRAGMA query_only(0)',
    'PRAGMA query_only = OFF',
  ]) {
    it(`refuses ${JSON.stringify(sql)} as a read-only violation`, async () => {
      const result = await callExecuteSql(sql);
      expect(result.isError).toBe(true);
      expect(result.payload.code).toBe('READONLY_VIOLATION');
      expect(userVersion()).toBe(0);
    });
  }
});
