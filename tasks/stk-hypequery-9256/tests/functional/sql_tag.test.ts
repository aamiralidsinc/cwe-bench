/**
 * The `sql` tagged template is the documented raw-SQL authoring helper: it
 * inserts what it is given as SQL text, so a column name or a number written
 * into it stays exactly what the caller wrote.
 */
import { describe, expect, it } from 'vitest';
import { sql } from '../../../../index.js';

describe('the sql tagged template keeps working', () => {
  it('inserts an interpolated column name verbatim', () => {
    const column = 'created_at';
    expect(sql`DATE(${column})`.sql).toBe('DATE(created_at)');
  });

  it('inserts an interpolated number verbatim', () => {
    const days = 7;
    expect(sql`created_at >= NOW() - INTERVAL ${days} DAY`.sql).toBe(
      'created_at >= NOW() - INTERVAL 7 DAY'
    );
  });

  it('inserts a nested expression verbatim', () => {
    const dateExpr = sql`DATE(created_at)`;
    expect(sql`toHour(${dateExpr})`.sql).toBe('toHour(DATE(created_at))');
  });
});
