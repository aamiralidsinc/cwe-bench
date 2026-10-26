/**
 * The filter carried by a measure is a value like any other: it is carried
 * inside one string literal in the SQL that the metric executor builds.
 */
import { describe, expect, it } from 'vitest';
import { baselineMetricSql, metricSql } from '../lib/datasets.js';
import { normalizedShape, stringLiterals } from '../lib/sqlcheck.js';

function measureFilterIsData(payload: string, measure: 'completedRevenue' | 'listedRevenue' = 'completedRevenue'): void {
  let sql: string;
  try {
    sql = metricSql(payload, measure);
  } catch {
    return; // refusing the request is an acceptable answer
  }
  expect(normalizedShape(sql)).toEqual(normalizedShape(baselineMetricSql(measure)));
  expect(stringLiterals(sql)).toContain(payload);
}

describe('a measure filter value stays inside its string literal', () => {
  it('keeps a value that ends with a backslash inside the literal', () => {
    measureFilterIsData('beta\\');
  });

  it('keeps a value that closes the literal with a backslash and a quote', () => {
    measureFilterIsData("x\\' OR 1=1 --");
  });

  it('keeps a value inside a list of filter values', () => {
    measureFilterIsData("x\\' OR 1=1 --", 'listedRevenue');
  });
});
