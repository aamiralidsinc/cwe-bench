import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';

vi.mock('mariadb', async () => {
  const { FakeMariaPool } = await import('../support/fake-mysql-family.ts');
  const createPool = (config: unknown) => new FakeMariaPool(config);
  return { default: { createPool }, createPool };
});

import { audit, resetAudit } from '../support/fake-mysql-family.ts';
import { connectSources, setReadonly, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/mariadb/index.js';

const source = {
  id: 'default',
  type: 'mariadb' as const,
  dsn: 'mariadb://app:app@db.example:3306/app',
};

describe('ordinary MariaDB use keeps working', () => {
  beforeAll(async () => {
    await connectSources([source], true);
  });
  beforeEach(() => {
    resetAudit();
    setReadonly(true);
  });

  it('a read-only tool returns rows for an ordinary query', async () => {
    const result = await callExecuteSql('SELECT * FROM users');
    expect(result.isError).toBe(false);
    expect(result.payload.data.rows.length).toBeGreaterThan(0);
  });

  it('a writable tool on the same source still writes', async () => {
    setReadonly(false);
    const result = await callExecuteSql("SELECT write_marker('writable')");
    expect(result.isError).toBe(false);
    expect(audit.writes).toEqual(['writable']);
  });

  it('a writable tool still writes right after a read-only call', async () => {
    await callExecuteSql('SELECT * FROM users');
    setReadonly(false);
    await callExecuteSql("SELECT write_marker('after-readonly')");
    expect(audit.writes).toEqual(['after-readonly']);
  });
});
