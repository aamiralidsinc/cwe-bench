/**
 * Ordinary values keep binding exactly as they do today.
 */
import { describe, expect, it } from 'vitest';
import { makeDb } from '../lib/harness.js';
import { stringLiterals } from '../lib/sqlcheck.js';

function sqlFor(value: unknown, op: 'eq' | 'like' = 'eq'): string {
  const { db } = makeDb();
  return db.table('events').select(['id']).where('name', op, value).toSQL();
}

describe('ordinary values keep working', () => {
  it('doubles a quote in a string value', () => {
    expect(sqlFor("O'Brien")).toBe("SELECT id FROM events WHERE name = 'O''Brien'");
  });

  it('carries a LIKE pattern unchanged', () => {
    expect(sqlFor("%O'Brien%", 'like')).toBe("SELECT id FROM events WHERE name LIKE '%O''Brien%'");
  });

  it('carries a value containing a question mark', () => {
    expect(sqlFor('what?')).toBe("SELECT id FROM events WHERE name = 'what?'");
    expect(sqlFor('%?%', 'like')).toBe("SELECT id FROM events WHERE name LIKE '%?%'");
  });

  it('carries non-ASCII text unchanged', () => {
    const value = 'héllo 世界 🚀';
    expect(stringLiterals(sqlFor(value))).toContain(value);
  });

  it('renders numbers, booleans and dates', () => {
    expect(sqlFor(42)).toBe('SELECT id FROM events WHERE name = 42');
    expect(sqlFor(true)).toBe('SELECT id FROM events WHERE name = true');
    expect(sqlFor(new Date('2024-01-01T00:00:00.000Z'))).toBe(
      "SELECT id FROM events WHERE name = '2024-01-01T00:00:00.000Z'"
    );
  });

  it('carries an ordinary object or array as JSON', () => {
    expect(stringLiterals(sqlFor({ note: 'benign', count: 2 }))).toContain('{"note":"benign","count":2}');
    expect(stringLiterals(sqlFor(['a', 'b']))).toContain('["a","b"]');
  });
});
