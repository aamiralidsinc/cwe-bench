import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';

vi.mock('mariadb', async () => {
  const { FakeMariaPool } = await import('../support/fake-mysql-family.ts');
  const createPool = (config: unknown) => new FakeMariaPool(config);
  return { default: { createPool }, createPool };
});

import { audit, resetAudit } from '../support/fake-mysql-family.ts';
import { connectSources, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/mariadb/index.js';

const source = {
  id: 'default',
  type: 'mariadb' as const,
  dsn: 'mariadb://app:app@db.example:3306/app',
};

describe('a read-only MariaDB tool cannot write through an allowed statement', () => {
  beforeAll(async () => {
    await connectSources([source], true);
  });
  beforeEach(() => resetAudit());

  it('a function called from a SELECT does not take effect', async () => {
    await callExecuteSql("SELECT write_marker('maria')");
    expect(audit.writes).toEqual([]);
  });

  it('a function in a second batch statement does not take effect', async () => {
    await callExecuteSql("SELECT 1; SELECT write_marker('maria-batch')");
    expect(audit.writes).toEqual([]);
  });

  it('a function nested inside a scalar subquery does not take effect', async () => {
    await callExecuteSql("SELECT (SELECT write_marker('maria-nested')) AS value");
    expect(audit.writes).toEqual([]);
  });
});
