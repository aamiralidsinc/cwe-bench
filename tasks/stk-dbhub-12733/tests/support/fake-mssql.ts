/**
 * A small in-process stand-in for a SQL Server pool. SQL Server has no read-only
 * transaction, so the connector itself must refuse a write when the tool is
 * read-only; if the write reaches this stand-in it is recorded as having run.
 */

export const audit = {
  writes: [] as string[],
  log: [] as string[],
};

export function resetAudit(): void {
  audit.writes.length = 0;
  audit.log.length = 0;
}

let inTransaction = false;
let pending: string[] = [];

export function resetTransaction(): void {
  inTransaction = false;
  pending = [];
}

const WRITE_STMT = /^\s*(insert|update|delete|merge|create|drop|alter|truncate|exec|execute)\b/i;

class FakeRequest {
  on(): this {
    return this;
  }
  input(): this {
    return this;
  }
  async query(sql: unknown) {
    return run(String(sql));
  }
  async batch(sql: unknown) {
    return run(String(sql));
  }
}

function run(sql: string) {
  const text = sql.trim();
  audit.log.push(text);
  let rows: any[] = [];
  let affected: number[] = [0];
  for (const part of text.split(';').map((s) => s.trim()).filter(Boolean)) {
    const upper = part.toUpperCase();
    if (/^BEGIN\s+TRAN(SACTION)?$/.test(upper)) {
      inTransaction = true;
      pending = [];
      continue;
    }
    if (/^COMMIT(\s+TRAN(SACTION)?)?$/.test(upper)) {
      audit.writes.push(...pending);
      pending = [];
      inTransaction = false;
      continue;
    }
    if (/^ROLLBACK(\s+TRAN(SACTION)?)?$/.test(upper)) {
      pending = [];
      inTransaction = false;
      continue;
    }
    if (WRITE_STMT.test(part)) {
      if (inTransaction) pending.push(part);
      else audit.writes.push(part);
      affected = [1];
      continue;
    }
    rows = [{ one: 1 }];
    affected = [1];
  }
  return { recordset: rows, rowsAffected: affected };
}

export class FakeConnectionPool {
  constructor(public readonly config: unknown) {}
  async connect(): Promise<FakeConnectionPool> {
    return this;
  }
  request(): FakeRequest {
    return new FakeRequest();
  }
  async close(): Promise<void> {}
}

export const VarChar = "varchar";
export const Int = "int";
export const Float = "float";
export const Bit = "bit";
