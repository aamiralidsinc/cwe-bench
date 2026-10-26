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

import { audit, resetAudit, resetTransaction } from '../support/fake-mssql.ts';
import { SQLServerConnector } from '../../src/connectors/sqlserver/index.js';

let connector: SQLServerConnector;

describe('a read-only SQL Server execution cannot write', () => {
  beforeAll(async () => {
    connector = new SQLServerConnector();
    await connector.connect('sqlserver://app:app@db.example:1433/app?sslmode=disable');
  });
  beforeEach(() => { resetAudit(); resetTransaction(); });

  it('an INSERT handed to a read-only execution does not take effect', async () => {
    try {
      await connector.executeSQL('INSERT INTO audit_log(msg) VALUES (1)', { readonly: true });
    } catch {
      /* a refusal is one acceptable outcome */
    }
    expect(audit.writes).toEqual([]);
  });

  it('an UPDATE in the second statement of a read-only batch does not take effect', async () => {
    try {
      await connector.executeSQL('SELECT 1; UPDATE audit_log SET msg = 1', { readonly: true });
    } catch {
      /* a refusal is one acceptable outcome */
    }
    expect(audit.writes).toEqual([]);
  });

  it('a DELETE handed to a read-only execution does not take effect', async () => {
    try {
      await connector.executeSQL('DELETE FROM audit_log', { readonly: true });
    } catch {
      /* a refusal is one acceptable outcome */
    }
    expect(audit.writes).toEqual([]);
  });
});
