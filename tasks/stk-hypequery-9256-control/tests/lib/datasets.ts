/**
 * A metrics dataset whose measure carries a filter, built through the
 * datasets package's public helpers and compiled by its metric executor.
 */
import { dataset, dimension, measure, MetricExecutor } from '../../../../../../datasets/src/index.js';
import { makeDb } from './harness.js';

function buildDataset(filterValue: unknown) {
  return dataset('orders', {
    source: 'orders',
    timeKey: 'created_at',
    dimensions: {
      id: dimension.string(),
      status: dimension.string(),
      country: dimension.string(),
      amount: dimension.number(),
      createdAt: dimension.timestamp(),
    },
    measures: {
      completedRevenue: measure.sum('amount', {
        filters: [{ field: 'status', operator: 'eq', value: filterValue }],
      }),
      listedRevenue: measure.sum('amount', {
        filters: [{ field: 'status', operator: 'in', value: ['completed', filterValue] }],
      }),
    },
    filters: {
      status: { __type: 'filter_definition', field: 'status', operators: ['eq', 'in'] },
    },
  } as any);
}

/**
 * SQL for a metric whose filtered measure carries `filterValue`, compiled by
 * the package's own MetricExecutor over a real query builder.
 */
export function metricSql(filterValue: unknown, measureName: 'completedRevenue' | 'listedRevenue' = 'completedRevenue'): string {
  const ds = buildDataset(filterValue) as any;
  const metric = ds.metric(measureName, { measure: measureName });
  const { db } = makeDb();
  const executor = new MetricExecutor({ builderFactory: db } as any);
  return executor.toSQL(metric, { dimensions: ['country'] }) as string;
}

/** SQL for the metric with a filter supplied on the query itself. */
export function metricSqlWithQueryFilter(filterValue: unknown): string {
  const ds = buildDataset('completed') as any;
  const metric = ds.metric('completedRevenue', { measure: 'completedRevenue' });
  const { db } = makeDb();
  const executor = new MetricExecutor({ builderFactory: db } as any);
  return executor.toSQL(metric, {
    dimensions: ['country'],
    filters: [{ field: 'status', operator: 'eq', value: filterValue }],
  }) as string;
}

/** A metric with a normal filter value, for comparison. */
export function baselineMetricSql(measureName: 'completedRevenue' | 'listedRevenue' = 'completedRevenue'): string {
  return metricSql('completed', measureName);
}
