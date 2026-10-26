/**
 * A name a caller supplies (a function name, a CTE name, a column, a table or a
 * row count) is written into the statement as a name only; it cannot add SQL
 * around it.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { normalizedShape } from '../lib/sqlcheck.js';

function shapeOf(build: () => string): string[] | null {
  try {
    return normalizedShape(build());
  } catch {
    return null; // refusing the request is an acceptable answer
  }
}

function unchangedStructure(build: (name: string) => string, attack: string, benign: string): void {
  const attacked = shapeOf(() => build(attack));
  if (attacked === null) return;
  expect(attacked).toEqual(shapeOf(() => build(benign)));
}

describe('a supplied name is written as a name only', () => {
  it('rejects a function name that closes the call and adds a condition', () => {
    const { db } = makeDb();
    unchangedStructure(
      name =>
        db
          .table('events')
          .select(['id'])
          .where((expr: any) => expr.fn(name, 'name'))
          .toSQL(),
      'startsWith) OR 1=1 --',
      'startsWith'
    );
  });

  it('rejects a CTE name that closes the CTE and adds another', () => {
    const { db } = makeDb();
    unchangedStructure(
      name => db.table('events').select(['id']).withCTE(name, 'SELECT 1').toSQL(),
      'recent AS (SELECT 1), extra',
      'recent'
    );
  });

  it('rejects an order-by column that ends the statement', () => {
    const { db } = makeDb();
    unchangedStructure(
      name => db.table('events').select(['id']).orderBy(name, 'DESC').toSQL(),
      'id; DROP TABLE events',
      'id'
    );
  });

  it('rejects a group-by column that closes the clause', () => {
    const { db } = makeDb();
    unchangedStructure(
      name => db.table('events').select(['id']).groupBy(name).toSQL(),
      'id) UNION SELECT 1 FROM secret --',
      'id'
    );
  });

  it('rejects a row limit that is not a number', () => {
    const { db } = makeDb();
    unchangedStructure(
      name => db.table('events').select(['id']).limit(name as any).toSQL(),
      '10 UNION SELECT 1',
      '10'
    );
  });

  it('rejects a table name that ends the statement', () => {
    const { db } = makeDb();
    unchangedStructure(
      name => db.table(name).select(['id']).toSQL(),
      'events; DROP TABLE users',
      'events'
    );
  });
});
