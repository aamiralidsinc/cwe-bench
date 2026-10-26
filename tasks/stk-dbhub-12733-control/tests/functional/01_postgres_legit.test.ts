import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';

vi.mock('pg', async () => {
  const { FakePgPool } = await import('../support/fake-pg.ts');
  return { default: { Pool: FakePgPool }, Pool: FakePgPool };
});

import { audit, resetAudit } from '../support/fake-pg.ts';
import { connectSources, setReadonly, callExecuteSql } from '../support/harness.ts';
import '../../src/connectors/postgres/index.js';

const source = {
  id: 'default',
  type: 'postgres' as const,
  dsn: 'postgres://app:app@db.example:5432/app',
};

describe('ordinary PostgreSQL use keeps working', () => {
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
    const result = await callExecuteSql("SELECT record_write('writable')");
    expect(result.isError).toBe(false);
    expect(audit.writes).toEqual(['writable']);
  });

  it('a writable tool still writes right after a read-only call', async () => {
    await callExecuteSql('SELECT * FROM users');
    setReadonly(false);
    await callExecuteSql("SELECT record_write('after-readonly')");
    expect(audit.writes).toEqual(['after-readonly']);
  });
});
