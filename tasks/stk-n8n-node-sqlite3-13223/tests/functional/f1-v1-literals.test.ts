import fs from 'fs';
import path from 'path';
import { SqliteV1 } from '../../nodes/SqliteNode/v1/SqliteV1.node';
import { JsonObject, loadNodeParameters, makeContext } from '../support/n8n-params';
import { makeCaseDir, makeFile, removeCaseDir } from '../support/fixtures';

const FakeDatabase = require('../support/fake-better-sqlite3.js');
const records: Array<{ file: string; options: Record<string, unknown> }> = FakeDatabase.__records;

const baseParams: JsonObject = {
  query: 'SELECT 1',
  args: '{}',
  query_type: 'SELECT',
  spread: false,
  additionalOptions: {},
};

async function runV1(raw: JsonObject): Promise<void> {
  const node = new SqliteV1();
  const loaded = loadNodeParameters(node.description.properties, raw);
  const ctx = makeContext(loaded, [{}]);
  await node.execute.call(ctx as never);
}

beforeEach(() => {
  records.length = 0;
});

describe('literal database paths keep working', () => {
  test('a relative path still selects that file', async () => {
    const base = makeCaseDir();
    const previous = process.cwd();
    try {
      process.chdir(base);
      await runV1({ ...baseParams, db_path: 'test.sqlite' });
      expect(records).toHaveLength(1);
      expect(records[0].file).toBe('test.sqlite');
    } finally {
      process.chdir(previous);
      removeCaseDir(base);
    }
  });

  test('an absolute path whose parent does not exist still creates the parent', async () => {
    const base = makeCaseDir();
    try {
      const file = path.join(base, 'nested', 'deeper', 'store.sqlite');
      await runV1({ ...baseParams, db_path: file });
      expect(fs.statSync(path.dirname(file)).isDirectory()).toBe(true);
      expect(records).toHaveLength(1);
      expect(records[0].file).toBe(file);
    } finally {
      removeCaseDir(base);
    }
  });

  test('a literal custom bindings path is still passed to the driver', async () => {
    const base = makeCaseDir();
    try {
      const bindings = makeFile(path.join(base, 'bindings', 'better_sqlite3.node'));
      await runV1({
        ...baseParams,
        db_path: path.join(base, 'store.sqlite'),
        additionalOptions: { use_custom_bindings: bindings },
      });
      expect(records).toHaveLength(1);
      expect(records[0].options.nativeBinding).toBe(bindings);
    } finally {
      removeCaseDir(base);
    }
  });

  test('the default bindings choice still passes no override', async () => {
    const base = makeCaseDir();
    try {
      await runV1({
        ...baseParams,
        db_path: path.join(base, 'store.sqlite'),
        additionalOptions: { use_default_bindings: true },
      });
      expect(records).toHaveLength(1);
      expect(records[0].options.nativeBinding).toBeUndefined();
    } finally {
      removeCaseDir(base);
    }
  });
});
