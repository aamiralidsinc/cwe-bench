/**
 * Ordinary names — plain columns, dotted columns, CTE names, function names and
 * whole-number limits — keep working exactly as they do today.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';

describe('ordinary names keep working', () => {
  it('orders by a plain column and a dotted column', () => {
    const { db } = makeDb();
    expect(db.table('events').select(['id']).orderBy('price', 'DESC').toSQL()).toBe(
      'SELECT id FROM events ORDER BY price DESC'
    );
    expect(db.table('events').select(['id']).orderBy('users.user_name', 'ASC').toSQL()).toBe(
      'SELECT id FROM events ORDER BY users.user_name ASC'
    );
  });

  it('groups by plain and dotted columns', () => {
    const { db } = makeDb();
    expect(db.table('events').select(['name']).groupBy(['name', 'users.user_name']).toSQL()).toBe(
      'SELECT name FROM events GROUP BY name, users.user_name'
    );
  });

  it('names a CTE with a plain alias', () => {
    const { db } = makeDb();
    expect(db.table('events').select(['id']).withCTE('recent_ids', 'SELECT id FROM users').toSQL()).toBe(
      'WITH recent_ids AS (SELECT id FROM users) SELECT id FROM events'
    );
  });

  it('names a CTE built from another query', () => {
    const { db } = makeDb();
    const subquery = db.table('users').select(['id']).where('active', 'eq', 1);
    expect(db.table('events').select(['id']).withCTE('recent_ids', subquery).toSQL()).toBe(
      'WITH recent_ids AS (SELECT id FROM users WHERE active = 1) SELECT id FROM events'
    );
  });

  it('calls an ordinary function by name', () => {
    const { db } = makeDb();
    expect(db.table('events').select(['id']).where((expr: any) => expr.fn('startsWith', 'name')).toSQL()).toBe(
      'SELECT id FROM events WHERE startsWith(name)'
    );
  });

  it('takes whole-number limits and offsets', () => {
    const { db } = makeDb();
    expect(db.table('events').select(['id']).limit(10).offset(20).toSQL()).toBe(
      'SELECT id FROM events LIMIT 10 OFFSET 20'
    );
    expect(db.table('events').select(['id']).limitBy(5, 'id').toSQL()).toBe(
      'SELECT id FROM events LIMIT 5 BY id'
    );
  });

  it('keeps a plain scalar name working', () => {
    const { db } = makeDb();
    const sql = db
      .table('events')
      .select(['id'])
      .withScalar('total' as any, (expr: any) => expr.fn('count', expr.col('id')))
      .toSQL();
    expect(sql).toBe('WITH count(id) AS total SELECT id FROM events');
  });

  it('reads from an ordinary table name', () => {
    const { db } = makeDb();
    expect(db.table('events').select(['id']).toSQL()).toBe('SELECT id FROM events');
  });
});
