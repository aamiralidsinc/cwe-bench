/**
 * A small in-process stand-in for a MySQL/MariaDB session. It models the engine
 * behaviours the hidden suites need:
 *   - `START TRANSACTION READ ONLY` makes DML fail until COMMIT/ROLLBACK;
 *   - DDL performs an implicit commit, so it runs even inside a read-only
 *     transaction (MySQL/MariaDB semantics);
 *   - `--` starts a comment only when followed by whitespace, a control
 *     character or end of input, so `SELECT 1--1;DROP ...` is two statements;
 *   - `SELECT write_marker('x')` models a stored function with a side effect.
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

const WRITE_FN = /\bwrite_marker\s*\(\s*'([^']*)'/i;
const DDL = /^\s*(create|drop|alter|truncate|rename)\b/i;
const DML = /^\s*(insert|update|delete|replace|merge)\b/i;

/** Split a batch the way MySQL/MariaDB lex it: semicolons outside quotes; `--` needs whitespace. */
export function splitMySqlBatch(text: string): string[] {
  const out: string[] = [];
  let start = 0;
  let i = 0;
  while (i < text.length) {
    const c = text[i];
    if (c === "'" || c === '"' || c === "`") {
      const quote = c;
      i++;
      while (i < text.length) {
        if (text[i] === quote) {
          if (text[i + 1] === quote) {
            i += 2;
            continue;
          }
          i++;
          break;
        }
        if (text[i] === "\\" && quote !== "`") i++;
        i++;
      }
      continue;
    }
    if (c === "-" && text[i + 1] === "-") {
      const next = text[i + 2];
      if (next === undefined || next.charCodeAt(0) <= 0x20 || next.charCodeAt(0) === 0x7f) {
        while (i < text.length && text[i] !== "\n") i++;
        continue;
      }
      i += 2;
      continue;
    }
    if (c === "/" && text[i + 1] === "*") {
      // `/*!` and `/*M!` are executable in MySQL/MariaDB; leave their body as text.
      const next = text[i + 2];
      const nextNext = text[i + 3];
      if (next === "!" || (next === "M" && nextNext === "!")) {
        i += next === "!" ? 3 : 4;
        continue;
      }
      const close = text.indexOf("*/", i + 2);
      i = close < 0 ? text.length : close + 2;
      continue;
    }
    if (c === ";") {
      const statement = text.slice(start, i).trim();
      if (statement) out.push(statement);
      start = i + 1;
      i++;
      continue;
    }
    i++;
  }
  const tail = text.slice(start).trim();
  if (tail) out.push(tail);
  return out;
}

interface ExecResult {
  rows: any[];
  header: { affectedRows: number; insertId: number; fieldCount: number } | null;
}

class FakeConnection {
  private readOnly = false;
  private pendingReadOnly = false;

  async query(first: unknown, _params?: unknown): Promise<unknown> {
    const text = typeof first === "string" ? first : String((first as any).sql ?? "");
    audit.log.push(text);
    const statements = splitMySqlBatch(text);
    const results: ExecResult[] = [];
    for (const statement of statements) {
      results.push(this.execute(statement));
    }
    return this.format(results);
  }

  private execute(statement: string): ExecResult {
    const upper = statement.trim().toUpperCase();
    if (/^SET\s+TRANSACTION\s+READ\s+ONLY$/.test(upper)) {
      this.pendingReadOnly = true;
      return { rows: [], header: null };
    }
    if (/^START\s+TRANSACTION(\s+READ\s+ONLY)?$/.test(upper)) {
      this.readOnly = upper.includes("READ ONLY") || this.pendingReadOnly;
      this.pendingReadOnly = false;
      return { rows: [], header: null };
    }
    if (/^(COMMIT|ROLLBACK)$/.test(upper)) {
      this.readOnly = false;
      return { rows: [], header: null };
    }
    const fn = WRITE_FN.exec(statement);
    if (fn) {
      if (this.readOnly) {
        audit.blocked.push(fn[1]);
        throw new Error("Cannot execute statement in a READ ONLY transaction");
      }
      audit.writes.push(fn[1]);
      return { rows: [{ write_marker: 1 }], header: null };
    }
    if (DDL.test(statement)) {
      // DDL implicitly commits, ending any read-only transaction.
      this.readOnly = false;
      audit.writes.push("ddl:" + statement.trim());
      return { rows: [], header: { affectedRows: 0, insertId: 0, fieldCount: 0 } };
    }
    if (DML.test(statement)) {
      if (this.readOnly) {
        audit.blocked.push("dml");
        throw new Error("Cannot execute statement in a READ ONLY transaction");
      }
      audit.writes.push("dml:" + statement.trim());
      return { rows: [], header: { affectedRows: 1, insertId: 0, fieldCount: 0 } };
    }
    if (/^\s*(select|show|describe|desc|explain)\b/i.test(statement)) {
      return { rows: [{ one: 1 }], header: null };
    }
    return { rows: [], header: { affectedRows: 0, insertId: 0, fieldCount: 0 } };
  }

  protected format(_results: ExecResult[]): unknown {
    throw new Error("not implemented");
  }

  release(): void {}
}

class FakeMysqlConnection extends FakeConnection {
  protected format(results: ExecResult[]): unknown {
    const shape = (r: ExecResult) => (r.header ? r.header : r.rows);
    if (results.length === 1) return [shape(results[0]), []];
    return [results.map(shape), []];
  }
}

class FakeMariaConnection extends FakeConnection {
  protected format(results: ExecResult[]): unknown {
    const shape = (r: ExecResult) => (r.header ? r.header : r.rows);
    if (results.length === 1) return shape(results[0]);
    return results.map(shape);
  }
}

export class FakeMysqlPool {
  constructor(public readonly config: unknown) {}
  async query(sql: unknown, params?: unknown) {
    return new FakeMysqlConnection().query(sql, params);
  }
  async getConnection() {
    return new FakeMysqlConnection();
  }
  async end(): Promise<void> {}
  on(): void {}
}

export class FakeMariaPool {
  constructor(public readonly config: unknown) {}
  async query(sql: unknown, params?: unknown) {
    return new FakeMariaConnection().query(sql, params);
  }
  async getConnection() {
    return new FakeMariaConnection();
  }
  async end(): Promise<void> {}
  on(): void {}
}
