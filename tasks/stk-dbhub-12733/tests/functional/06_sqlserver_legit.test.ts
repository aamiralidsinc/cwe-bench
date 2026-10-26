import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';

vi.mock('mssql', async () => {
  const m = await import('../support/fake-mssql.ts');
  const ns = {
    ConnectionPool: m.FakeConnectionPool,
    VarChar: m.VarChar,
    Int: m.Int,
    Float: m.Float,
    Bit: m.Bit,
  };
  return { default: ns, ...ns };
});

import { audit, resetAudit } from '../support/fake-mssql.ts';
import { connectSources, setReadonly, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/sqlserver/index.js';

const source = {
  id: 'default',
  type: 'sqlserver' as const,
  dsn: 'sqlserver://app:app@db.example:1433/app?sslmode=disable',
};

describe('ordinary SQL Server use keeps working', () => {
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

  it('EXPLAIN still returns a plan in read-only mode', async () => {
    const result = await callExecuteSql('EXPLAIN SELECT * FROM users');
    expect(result.isError).toBe(false);
    expect(result.payload.data.rows.length).toBeGreaterThan(0);
  });

  it('a writable tool on the same source still writes', async () => {
    setReadonly(false);
    const result = await callExecuteSql('INSERT INTO users(id) VALUES (1)');
    expect(result.isError).toBe(false);
    expect(audit.writes).toHaveLength(1);
  });

  it('a writable tool still writes right after a read-only call', async () => {
    await callExecuteSql('SELECT * FROM users');
    setReadonly(false);
    await callExecuteSql('INSERT INTO users(id) VALUES (2)');
    expect(audit.writes).toHaveLength(1);
  });
});
