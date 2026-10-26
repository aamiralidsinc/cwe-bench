import { describe, it, expect, beforeEach } from 'vitest';
import { SQLiteConnector } from '../../src/connectors/sqlite/index.js';

async function connect(): Promise<SQLiteConnector> {
  const connector = new SQLiteConnector();
  await connector.connect(
    'sqlite:///:memory:',
    'CREATE TABLE audit_log(id INTEGER PRIMARY KEY, msg TEXT);'
  );
  return connector;
}

async function rows(connector: SQLiteConnector): Promise<number> {
  const result = await connector.executeSQL('SELECT COUNT(*) AS n FROM audit_log', {});
  return Number((result.rows[0] as { n: number | bigint }).n);
}

describe('a read-only SQLite execution cannot write at the engine', () => {
  let connector: SQLiteConnector;

  beforeEach(async () => {
    connector = await connect();
  });

  it('an INSERT handed to a read-only execution does not take effect', async () => {
    try {
      await connector.executeSQL("INSERT INTO audit_log(msg) VALUES ('direct')", { readonly: true });
    } catch {
      /* a refusal is one acceptable outcome */
    }
    expect(await rows(connector)).toBe(0);
  });

  it('a batch that turns the engine guard off first still writes nothing', async () => {
    try {
      await connector.executeSQL(
        "PRAGMA query_only = OFF; INSERT INTO audit_log(msg) VALUES ('batch')",
        { readonly: true }
      );
    } catch {
      /* a refusal is one acceptable outcome */
    }
    expect(await rows(connector)).toBe(0);
  });
});
