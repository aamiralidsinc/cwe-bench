/**
 * A fragment placed among other conditions cannot swallow them: what follows it
 * is still part of the statement, so the conditions after it still apply.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { filterRows, type Row } from '../lib/where.js';

/** Build the statement; refusing the request is an acceptable answer. */
function buildOrRefuse(build: () => string): string | undefined {
  try {
    return build();
  } catch {
    return undefined;
  }
}

const rows: Row[] = [
  { id: 1, tenant: 'TENANT-1', status: 'open' },
  { id: 2, tenant: 'TENANT-1', status: 'closed' },
  { id: 3, tenant: 'OTHER', status: 'open' },
];

describe('a fragment between conditions does not swallow them', () => {
  it('keeps a later condition after a fragment that ends in a line comment', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where((expr: any) => expr.raw('1=1 --'))
        .where('status', 'eq', 'open')
        .toSQL()
    );
    if (sql === undefined) return;
    const kept = filterRows(sql, rows);
    expect(kept.every(row => row.status === 'open')).toBe(true);
    expect(kept.every(row => row.tenant === 'TENANT-1')).toBe(true);
  });

  it('keeps conditions on both sides of a fragment that ends in a line comment', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where((expr: any) => expr.or([expr.raw("status = 'open' --"), expr.raw('1=0')]))
        .where('status', 'eq', 'open')
        .toSQL()
    );
    if (sql === undefined) return;
    const kept = filterRows(sql, rows);
    expect(kept.every(row => row.tenant === 'TENANT-1')).toBe(true);
  });

  it('keeps a condition after a fragment that ends in a hash comment', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where((expr: any) => expr.raw('1=1 # note'))
        .where('status', 'eq', 'open')
        .toSQL()
    );
    if (sql === undefined) return;
    const kept = filterRows(sql, rows);
    expect(kept.every(row => row.status === 'open')).toBe(true);
  });
});
