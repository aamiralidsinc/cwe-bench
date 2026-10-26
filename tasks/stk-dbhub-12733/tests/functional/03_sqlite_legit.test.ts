import { describe, it, expect, beforeAll, beforeEach } from 'vitest';
import { connectSources, setReadonly, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/sqlite/index.js';

const source = {
  id: 'default',
  type: 'sqlite' as const,
  dsn: 'sqlite:///:memory:',
  init_script: 'CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT); CREATE TABLE orders(id INTEGER PRIMARY KEY, user_id INTEGER);',
};

async function rowCount(): Promise<number> {
  const result = await callExecuteSql('SELECT COUNT(*) AS n FROM users');
  return result.isError ? -1 : Number(result.payload.data.rows[0].n);
}

describe('ordinary SQLite use keeps working', () => {
  beforeAll(async () => {
    await connectSources([source], true);
  });
  beforeEach(() => setReadonly(true));

  it('an in-memory source answers ordinary queries in read-only mode', async () => {
    const result = await callExecuteSql('SELECT * FROM users');
    expect(result.isError).toBe(false);
    expect(Array.isArray(result.payload.data.rows)).toBe(true);
  });

  it('schema discovery pragmas keep working in read-only mode', async () => {
    for (const sql of [
      'PRAGMA table_info(users)',
      'PRAGMA index_info(users)',
      'PRAGMA index_list(users)',
      'PRAGMA foreign_key_list(orders)',
      'PRAGMA user_version',
      'PRAGMA journal_mode',
    ]) {
      const result = await callExecuteSql(sql);
      expect(result.isError, sql).toBe(false);
    }
    const info = await callExecuteSql('PRAGMA table_info(users)');
    expect(info.payload.data.rows.length).toBe(2);
  });

  it('a writable tool on the same in-memory source still writes', async () => {
    setReadonly(false);
    const before = await rowCount();
    const inserted = await callExecuteSql("INSERT INTO users(id, name) VALUES (1, 'a')");
    expect(inserted.isError).toBe(false);
    expect(await rowCount()).toBe(before + 1);
  });

  it('a writable tool still writes right after a read-only call', async () => {
    await callExecuteSql('PRAGMA table_info(users)');
    setReadonly(false);
    const inserted = await callExecuteSql("INSERT INTO users(id, name) VALUES (2, 'b')");
    expect(inserted.isError).toBe(false);
    expect(await rowCount()).toBeGreaterThan(0);
  });
});
