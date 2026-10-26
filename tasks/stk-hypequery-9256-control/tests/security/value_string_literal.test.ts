/**
 * A filter value the caller supplies is carried inside one string literal, so
 * the value can never end that literal or add SQL around it.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { normalizedShape, stringLiterals } from '../lib/sqlcheck.js';

function render(payload: unknown, op: 'eq' | 'like' = 'eq'): string {
  const { db } = makeDb();
  return db
    .table('events')
    .select(['id'])
    .where('tenant', 'eq', 'TENANT-1')
    .where('name', op, payload)
    .toSQL();
}

function rendersAsOneLiteral(payload: string, op: 'eq' | 'like' = 'eq'): void {
  let sql: string;
  try {
    sql = render(payload, op);
  } catch {
    return; // refusing the request is an acceptable answer
  }
  expect(normalizedShape(sql)).toEqual(normalizedShape(render('benign', op)));
  expect(stringLiterals(sql)).toContain(payload);
}

describe('a supplied string value stays inside its string literal', () => {
  it('keeps a value that ends with a backslash inside the literal', () => {
    rendersAsOneLiteral('beta\\');
  });

  it('keeps a value that closes the literal with a backslash and a quote', () => {
    rendersAsOneLiteral("x\\' OR 1=1 --");
  });

  it('keeps a value made of backslashes and quotes', () => {
    rendersAsOneLiteral("\\\\' UNION SELECT 1 --");
  });

  it('keeps a backslash at the end of a LIKE pattern', () => {
    rendersAsOneLiteral('%\\', 'like');
  });

  it('keeps a backslash value separate from the value that follows it', () => {
    const { db } = makeDb();
    const build = (first: string, second: string) =>
      db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', first)
        .where('owner', 'eq', second)
        .toSQL();

    let sql: string;
    try {
      sql = build('TENANT-1\\', "' OR 1=1 --");
    } catch {
      return;
    }
    expect(normalizedShape(sql)).toEqual(normalizedShape(build('TENANT-1', 'owner')));
    expect(stringLiterals(sql)).toContain('TENANT-1\\');
    expect(stringLiterals(sql)).toContain("' OR 1=1 --");
  });

  it('sends no altered statement to the client for a backslash value', async () => {
    const { db, recorded } = makeDb({ rows: [] });
    try {
      await db
        .table('events')
        .select(['id'])
        .where('tenant', 'eq', 'TENANT-1')
        .where('name', 'eq', "x\\' OR 1=1 --")
        .execute();
    } catch {
      expect(recorded).toHaveLength(0);
      return;
    }
    for (const query of recorded) {
      expect(normalizedShape(query.sql)).toEqual(
        normalizedShape(
          (() => {
            const { db: clean } = makeDb();
            return clean
              .table('events')
              .select(['id'])
              .where('tenant', 'eq', 'TENANT-1')
              .where('name', 'eq', 'benign')
              .toSQL();
          })()
        )
      );
    }
  });
});
