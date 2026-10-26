import fs from 'fs';
import path from 'path';
import type { INodeTypeBaseDescription } from 'n8n-workflow';
import { SqliteV2 } from '../../nodes/SqliteNode/v2/SqliteV2.node';
import { SqliteCredentials } from '../../credentials/SqliteCredentials.credentials';
import { JsonObject, loadNodeParameters, makeContext, resolveCredentialData } from '../support/n8n-params';
import { makeCaseDir, removeCaseDir } from '../support/fixtures';

const FakeDatabase = require('../support/fake-better-sqlite3.js');
const records: Array<{ file: string; options: Record<string, unknown> }> = FakeDatabase.__records;

const baseDescription: INodeTypeBaseDescription = {
  displayName: 'SQLite',
  name: 'sqliteNode',
  group: ['transform'],
  description: 'SQLite',
};

function node(): SqliteV2 {
  return new SqliteV2(baseDescription);
}

function resolvedCredential(outside: string): JsonObject {
  const credential = new SqliteCredentials();
  return resolveCredentialData(
    credential.properties,
    { databasePath: '={{ $env.SQLITE_DB }}' },
    { env: { SQLITE_DB: outside } },
  );
}

function executionContext(outside: string) {
  const credentials = resolvedCredential(outside);
  const loaded = loadNodeParameters(node().description.properties, {
    resource: 'database',
    operation: 'executeQuery',
    query: 'SELECT 1',
    options: {},
  });
  return makeContext(loaded, [{}], { credentials, env: { SQLITE_DB: outside } });
}

function openedFiles(): string[] {
  return records.map((entry) => path.resolve(entry.file));
}

function expectUntouched(outside: string): void {
  expect(fs.existsSync(path.dirname(outside))).toBe(false);
  expect(openedFiles()).not.toContain(path.resolve(outside));
}

/** A refusal is a valid outcome; the assertions are about which file the product touched. */
async function attempt(work: () => Promise<unknown>): Promise<void> {
  try {
    await work();
  } catch {
    /* a controlled refusal is acceptable */
  }
}

beforeEach(() => {
  records.length = 0;
});

describe('stored database location written as an expression', () => {
  test('execution does not open the file the expression selects', async () => {
    const base = makeCaseDir();
    try {
      const outside = path.join(base, 'elsewhere', 'chosen.sqlite');
      await attempt(() => node().execute.call(executionContext(outside) as never));
      expectUntouched(outside);
    } finally {
      removeCaseDir(base);
    }
  });

  test('the connection check does not open the file the expression selects', async () => {
    const base = makeCaseDir();
    try {
      const outside = path.join(base, 'elsewhere', 'chosen.sqlite');
      const credentials = resolvedCredential(outside);
      await attempt(() =>
        node().methods.credentialTest.sqliteConnectionTest.call(
          {} as never,
          { data: credentials } as never,
        ),
      );
      expectUntouched(outside);
    } finally {
      removeCaseDir(base);
    }
  });

  test('the table search does not open the file the expression selects', async () => {
    const base = makeCaseDir();
    try {
      const outside = path.join(base, 'elsewhere', 'chosen.sqlite');
      const credentials = resolvedCredential(outside);
      const loaded = loadNodeParameters(node().description.properties, {
        resource: 'database',
        operation: 'select',
      });
      const ctx = makeContext(loaded, [{}], { credentials, env: { SQLITE_DB: outside } });
      await attempt(() => node().methods.listSearch.searchTables.call(ctx as never));
      expectUntouched(outside);
    } finally {
      removeCaseDir(base);
    }
  });

  test('the column lookup does not open the file the expression selects', async () => {
    const base = makeCaseDir();
    try {
      const outside = path.join(base, 'elsewhere', 'chosen.sqlite');
      const credentials = resolvedCredential(outside);
      const loaded = loadNodeParameters(node().description.properties, {
        resource: 'database',
        operation: 'select',
        table: 'employees',
      });
      const ctx = makeContext(loaded, [{}], { credentials, env: { SQLITE_DB: outside } });
      await attempt(() => node().methods.loadOptions.getColumns.call(ctx as never));
      expectUntouched(outside);
    } finally {
      removeCaseDir(base);
    }
  });
});
