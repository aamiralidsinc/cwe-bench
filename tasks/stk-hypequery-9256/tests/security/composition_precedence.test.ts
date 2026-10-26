/**
 * Conditions combined in one statement keep their own meaning: a group of
 * conditions joined with OR (or a fragment carrying one) binds to the
 * conditions around it, so a row that fails a later condition is never kept.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { filterHaving, filterRows, type Row } from '../lib/where.js';

const rows: Row[] = [
  { id: 1, tenant: 'TENANT-1', owner: 'me', is_public: 0, status: 'open', amount: 10 },
  { id: 2, tenant: 'OTHER', owner: 'nobody', is_public: 1, status: 'open', amount: -5 },
  { id: 3, tenant: 'TENANT-1', owner: 'nobody', is_public: 0, status: 'closed', amount: 10 },
  { id: 4, tenant: 'TENANT-1', owner: 'me', is_public: 1, status: 'closed', amount: 10 },
  { id: 5, tenant: 'OTHER', owner: 'me', is_public: 0, status: 'open', amount: 10 },
];

function keepWithinTenant(sql: string): void {
  const kept = filterRows(sql, rows);
  expect(kept.every(row => row.tenant === 'TENANT-1')).toBe(true);
}

/** Build the statement; refusing the request is an acceptable answer. */
function buildOrRefuse(build: () => string): string | undefined {
  try {
    return build();
  } catch {
    return undefined;
  }
}

describe('logical groups keep the meaning of the conditions around them', () => {
  it('keeps an OR group scoped when it follows another condition', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where((expr: any) => expr.or([expr.raw("owner = 'me'"), expr.raw('is_public = 1')]))
        .toSQL()
    );
    if (sql === undefined) return;
    keepWithinTenant(sql);
  });

  it('keeps an OR group scoped when a condition follows it', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where((expr: any) => expr.or([expr.raw("owner = 'me'"), expr.raw('is_public = 1')]))
        .where('tenant', 'eq', 'TENANT-1')
        .toSQL()
    );
    if (sql === undefined) return;
    keepWithinTenant(sql);
  });

  it('keeps a raw fragment carrying a top-level OR scoped', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where((expr: any) => expr.raw("owner = 'me' OR is_public = 1"))
        .toSQL()
    );
    if (sql === undefined) return;
    keepWithinTenant(sql);
  });

  it('keeps a nested logical group scoped', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where((expr: any) =>
          expr.or([expr.and([expr.raw("owner = 'me'"), expr.raw('is_public = 0')]), expr.raw('is_public = 1')])
        )
        .toSQL()
    );
    if (sql === undefined) return;
    keepWithinTenant(sql);
  });

  it('keeps a HAVING fragment carrying a top-level OR next to another fragment', () => {
    const { db } = makeDb();
    const sql = buildOrRefuse(() =>
      db
        .table('events')
        .select(['id'])
        .having('amount > 1 OR amount < 0')
        .having("status = 'open'")
        .toSQL()
    );
    if (sql === undefined) return;
    const kept = filterHaving(sql, rows);
    expect(kept.every(row => row.status === 'open')).toBe(true);
  });
});
