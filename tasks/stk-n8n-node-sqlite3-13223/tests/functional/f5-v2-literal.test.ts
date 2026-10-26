import fs from 'fs';
import path from 'path';
import type { INodeTypeBaseDescription } from 'n8n-workflow';
import { SqliteV2 } from '../../nodes/SqliteNode/v2/SqliteV2.node';
import { SqliteCredentials } from '../../credentials/SqliteCredentials.credentials';
import { loadNodeParameters, makeContext, resolveCredentialData } from '../support/n8n-params';
import { makeCaseDir, removeCaseDir } from '../support/fixtures';

const FakeDatabase = require('../support/fake-better-sqlite3.js');
const records: Array<{ file: string; options: Record<string, unknown> }> = FakeDatabase.__records;

const baseDescription: INodeTypeBaseDescription = {
  displayName: 'SQLite',
  name: 'sqliteNode',
  group: ['transform'],
  description: 'SQLite',
};

beforeEach(() => {
  records.length = 0;
});

describe('literal stored locations keep working', () => {
  test('a literal credential path opens that file and creates its parent', async () => {
    const base = makeCaseDir();
    try {
      const file = path.join(base, 'nested', 'deeper', 'store.sqlite');
      const credential = new SqliteCredentials();
      const credentials = resolveCredentialData(credential.properties, { databasePath: file });

      const node = new SqliteV2(baseDescription);
      const loaded = loadNodeParameters(node.description.properties, {
        resource: 'database',
        operation: 'executeQuery',
        query: 'SELECT 1',
        options: {},
      });
      const ctx = makeContext(loaded, [{}], { credentials });
      await node.execute.call(ctx as never);

      expect(fs.statSync(path.dirname(file)).isDirectory()).toBe(true);
      expect(records).toHaveLength(1);
      expect(records[0].file).toBe(file);
    } finally {
      removeCaseDir(base);
    }
  });
});
