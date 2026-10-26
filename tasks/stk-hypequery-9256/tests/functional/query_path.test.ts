/**
 * The statements the library actually sends keep working for ordinary input.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { stringLiterals } from '../lib/sqlcheck.js';

describe('the statement sent to the client keeps working', () => {
  it('runs an ordinary filtered query and returns its rows', async () => {
    const { db, recorded } = makeDb({ rows: [{ id: 1 }] });
    const rows = await db
      .table('events')
      .select(['id'])
      .where('tenant', 'eq', 'TENANT-1')
      .where('name', 'eq', "O'Brien")
      .execute();

    expect(rows).toEqual([{ id: 1 }]);
    expect(recorded).toHaveLength(1);
    expect(recorded[0]!.sql).toBe("SELECT id FROM events WHERE tenant = 'TENANT-1' AND name = 'O''Brien'");
  });

  it('sends a value with a quote and a percent sign unchanged', async () => {
    const { db, recorded } = makeDb();
    await db.table('events').select(['id']).where('name', 'like', "%50% O'Brien").execute();
    expect(stringLiterals(recorded[0]!.sql)).toContain("%50% O'Brien");
  });

  it('sends a statement with no parameters untouched', () => {
    const { db } = makeDb();
    const sql = db.table('events').select(['id']).where('active', 'eq', 1).toSQL();
    expect(sql).toBe('SELECT id FROM events WHERE active = 1');
  });
});
