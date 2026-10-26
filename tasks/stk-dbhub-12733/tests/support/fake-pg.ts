/**
 * A small in-process stand-in for a PostgreSQL session, used only by the hidden
 * suites. It models the one engine behaviour the tests care about: a statement
 * executed inside a READ ONLY transaction is refused, and a statement executed
 * outside one takes effect. `record_write('x')` models a stored function that
 * inserts a row; any statement that writes outside a read-only transaction is
 * recorded in `audit.writes`.
 */

export const audit = {
  writes: [] as string[],
  blocked: [] as string[],
  log: [] as string[],
};

export function resetAudit(): void {
  audit.writes.length = 0;
  audit.blocked.length = 0;
  audit.log.length = 0;
}

const WRITE_FN = /\brecord_write\s*\(\s*'([^']*)'/i;
const WRITE_STMT = /^\s*(insert|update|delete|replace|merge|create|drop|alter|truncate|grant|revoke)\b/i;

class FakePgClient {
  private readOnlyTx = false;

  async query(sql: unknown, _params?: unknown): Promise<{ rows: unknown[]; rowCount: number }> {
    const text = String(sql).trim();
    const upper = text.toUpperCase();
    audit.log.push(text);

    if (/^BEGIN\s+READ\s+ONLY$/.test(upper)) {
      this.readOnlyTx = true;
      return { rows: [], rowCount: 0 };
    }
    if (/^SET\s+TRANSACTION\s+READ\s+ONLY$/.test(upper)) {
      this.readOnlyTx = true;
      return { rows: [], rowCount: 0 };
    }
    if (/^(BEGIN|START\s+TRANSACTION)$/.test(upper)) {
      this.readOnlyTx = false;
      return { rows: [], rowCount: 0 };
    }
    if (/^(COMMIT|ROLLBACK)$/.test(upper)) {
      this.readOnlyTx = false;
      return { rows: [], rowCount: 0 };
    }

    const fn = WRITE_FN.exec(text);
    if (fn) {
      if (this.readOnlyTx) {
        audit.blocked.push(fn[1]);
        throw new Error("cannot execute SELECT in a read-only transaction");
      }
      audit.writes.push(fn[1]);
      return { rows: [{ record_write: true }], rowCount: 1 };
    }
    if (WRITE_STMT.test(text)) {
      if (this.readOnlyTx) {
        audit.blocked.push("statement");
        throw new Error("cannot execute a write in a read-only transaction");
      }
      audit.writes.push(text);
      return { rows: [], rowCount: 1 };
    }
    if (/^\s*select\b/i.test(text)) {
      return { rows: [{ one: 1 }], rowCount: 1 };
    }
    return { rows: [], rowCount: 0 };
  }

  release(): void {}
}

export class FakePgPool {
  constructor(public readonly config: unknown) {}
  async connect(): Promise<FakePgClient> {
    return new FakePgClient();
  }
  async query(sql: unknown, params?: unknown) {
    return new FakePgClient().query(sql, params);
  }
  async end(): Promise<void> {}
  on(): void {}
}
