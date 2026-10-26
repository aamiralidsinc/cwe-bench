/**
 * The product entry points these suites drive, and a recording ClickHouse
 * client so a test can see exactly what statement the library would run.
 */
import { createQueryBuilder } from '../../../../index.js';
import { createClickHouseAdapter } from '../../../../core/adapters/clickhouse-adapter.js';

export interface RecordedQuery {
  sql: string;
  rows?: unknown[];
}

export interface TestDb {
  db: any;
  recorded: RecordedQuery[];
  /** Clear what the client has been asked to run. */
  reset(): void;
}

/**
 * A query builder that talks to a recording client instead of a server. Every
 * statement the library sends is captured in `recorded`.
 */
export function makeDb(options: { rows?: unknown[] } = {}): TestDb {
  const recorded: RecordedQuery[] = [];
  const client = {
    query: async ({ query }: { query: string }) => {
      recorded.push({ sql: query });
      return {
        json: async () => options.rows ?? [],
        stream: () => null,
      };
    },
  };
  const db = createQueryBuilder({ adapter: createClickHouseAdapter({ client } as any) }) as any;
  return {
    db,
    recorded,
    reset() {
      recorded.length = 0;
    },
  };
}

/** Build a statement, or report that the library refused the input. */
export function tryBuild(build: () => string): { sql: string } | { refused: true } {
  try {
    return { sql: build() };
  } catch {
    return { refused: true };
  }
}
