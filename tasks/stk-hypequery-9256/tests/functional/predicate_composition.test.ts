/**
 * Ordinary conditions, fragments and groups keep the meaning they have today.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { filterHaving, filterRows, type Row } from '../lib/where.js';

const rows: Row[] = [
  { id: 1, tenant: 'TENANT-1', status: 'open', owner: 'me', is_public: 0, amount: 10 },
  { id: 2, tenant: 'TENANT-1', status: 'closed', owner: 'me', is_public: 0, amount: 10 },
  { id: 3, tenant: 'OTHER', status: 'open', owner: 'me', is_public: 1, amount: -5 },
];

describe('ordinary composition keeps working', () => {
  it('renders a flat AND sequence exactly as today', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .where('tenant', 'eq', 'TENANT-1')
      .where('status', 'eq', 'open')
      .toSQL();
    expect(sql).toBe("SELECT id FROM events WHERE tenant = 'TENANT-1' AND status = 'open'");
    expect(filterRows(sql, rows).map(row => row.id)).toEqual([1]);
  });

  it('renders a raw fragment without logical operators unchanged', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .where('tenant', 'eq', 'TENANT-1')
      .where((expr: any) => expr.raw('is_public = 0'))
      .toSQL();
    expect(sql).toBe("SELECT id FROM events WHERE tenant = 'TENANT-1' AND is_public = 0");
  });

  it('keeps an OR group as the only condition working', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .where((expr: any) => expr.or([expr.raw("owner = 'me'"), expr.raw('is_public = 1')]))
      .toSQL();
    expect(filterRows(sql, rows).map(row => row.id)).toEqual([1, 2, 3]);
  });

  it('keeps an AND group next to another condition working', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .where('tenant', 'eq', 'TENANT-1')
      .where((expr: any) => expr.and([expr.raw("owner = 'me'"), expr.raw('is_public = 0')]))
      .toSQL();
    expect(filterRows(sql, rows).map(row => row.id)).toEqual([1, 2]);
  });

  it('keeps an AND group as the only condition working', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .where((expr: any) => expr.and([expr.raw('is_public = 0'), expr.raw("tenant = 'TENANT-1'")]))
      .toSQL();
    expect(filterRows(sql, rows).map(row => row.id)).toEqual([1, 2]);
  });

  it('keeps a fragment ending in a line comment as the last condition working', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .where('tenant', 'eq', 'TENANT-1')
      .where((expr: any) => expr.raw('1=1 -- trailing note'))
      .toSQL();
    expect(filterRows(sql, rows).map(row => row.id)).toEqual([1, 2]);
  });

  it('renders a single HAVING fragment unchanged', () => {
    const { db } = makeDb();
    const sql = db.table('events').select(['id']).having('amount > 1').toSQL();
    expect(sql).toBe('SELECT id FROM events HAVING amount > 1');
    expect(filterHaving(sql, rows).map(row => row.id)).toEqual([1, 2]);
  });

  it('keeps two HAVING fragments that carry no logical operator working', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .having('amount > 1')
      .having("status = 'open'")
      .toSQL();
    expect(filterHaving(sql, rows).map(row => row.id)).toEqual([1]);
  });
});
