import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';

vi.mock('pg', async () => {
  const { FakePgPool } = await import('../support/fake-pg.ts');
  return { default: { Pool: FakePgPool }, Pool: FakePgPool };
});

import { audit, resetAudit } from '../support/fake-pg.ts';
import { connectSources, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/postgres/index.js';

const source = {
  id: 'default',
  type: 'postgres' as const,
  dsn: 'postgres://app:app@db.example:5432/app',
};

describe('a read-only PostgreSQL tool cannot write through an allowed statement', () => {
  beforeAll(async () => {
    await connectSources([source], true);
  });
  beforeEach(() => resetAudit());

  it('a function called from a SELECT does not take effect', async () => {
    await callExecuteSql("SELECT record_write('seq-reset')");
    expect(audit.writes).toEqual([]);
  });

  it('a function called from a data-selecting CTE does not take effect', async () => {
    await callExecuteSql("WITH picked AS (SELECT record_write('cte')) SELECT * FROM picked");
    expect(audit.writes).toEqual([]);
  });

  it('a function in the second statement of a batch does not take effect', async () => {
    await callExecuteSql("SELECT 1; SELECT record_write('batched')");
    expect(audit.writes).toEqual([]);
  });
  it('a function nested in a scalar subquery does not take effect', async () => {
    await callExecuteSql("SELECT (SELECT record_write('nested')) AS value");
    expect(audit.writes).toEqual([]);
  });
});
