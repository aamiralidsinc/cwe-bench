/**
 * Ordinary measure filters keep compiling to the same SQL, and request filters
 * keep binding as parameters.
 */
import { describe, expect, it } from 'vitest';
import { baselineMetricSql, metricSql, metricSqlWithQueryFilter } from '../lib/datasets.js';

describe('ordinary measure filters keep working', () => {
  it('renders a filtered measure exactly as today', () => {
    expect(baselineMetricSql()).toContain("SUM(if((status = 'completed'), amount, 0)) AS completedRevenue");
  });

  it('renders a list filter exactly as today', () => {
    expect(metricSql('pending', 'listedRevenue')).toContain(
      "SUM(if((status IN ('completed', 'pending')), amount, 0)) AS listedRevenue"
    );
  });

  it('keeps a request filter bound as a parameter', () => {
    const sql = metricSqlWithQueryFilter("O'Brien");
    expect(sql).toContain('status = ?');
    expect(sql).not.toContain("O'Brien");
  });
});
