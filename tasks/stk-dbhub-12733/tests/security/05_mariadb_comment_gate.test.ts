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

describe('the read-only admission decision sees every statement the engine runs', () => {
  beforeAll(async () => {
    await connectSources([source], true);
  });
  beforeEach(() => resetAudit());

  it('a DROP written after a minus-minus run is refused', async () => {
    const result = await callExecuteSql('SELECT 1--1;DROP TABLE victim');
    expect(result.isError).toBe(true);
    expect(result.payload.code).toBe('READONLY_VIOLATION');
    expect(audit.writes).toEqual([]);
  });

  it('an INSERT written after a minus-minus run is refused', async () => {
    const result = await callExecuteSql("SELECT 1--1;INSERT INTO audit_log(msg) VALUES ('hidden')");
    expect(result.isError).toBe(true);
    expect(result.payload.code).toBe('READONLY_VIOLATION');
    expect(audit.writes).toEqual([]);
  });
});
