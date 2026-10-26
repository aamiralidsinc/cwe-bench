/**
 * A structured value (an object or an array) is still a value: the JSON text
 * that represents it is carried inside one string literal.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { normalizedShape, stringLiterals } from '../lib/sqlcheck.js';

function render(payload: unknown): string {
  const { db } = makeDb();
  return db
    .table('events')
    .select(['id'])
    .where('tenant', 'eq', 'TENANT-1')
    .where('meta', 'eq', payload)
    .toSQL();
}

function structuredValueIsData(payload: unknown, benign: unknown): void {
  let sql: string;
  try {
    sql = render(payload);
  } catch {
    return; // refusing the request is an acceptable answer
  }
  expect(normalizedShape(sql)).toEqual(normalizedShape(render(benign)));
  expect(stringLiterals(sql)).toContain(JSON.stringify(payload));
}

describe('a supplied structured value stays inside its string literal', () => {
  it('keeps an object holding a quote inside the literal', () => {
    structuredValueIsData({ note: "x' OR 1=1 --" }, { note: 'benign' });
  });

  it('keeps an array holding a quote inside the literal', () => {
    structuredValueIsData(["x' OR 1=1 --"], ['benign']);
  });

  it('keeps a nested object holding a quote inside the literal', () => {
    structuredValueIsData({ outer: { inner: "') UNION SELECT 1 --" } }, { outer: { inner: 'benign' } });
  });

  it('keeps an object holding a backslash before a quote inside the literal', () => {
    structuredValueIsData({ note: "x\\' OR 1=1 --" }, { note: 'benign' });
  });
});
