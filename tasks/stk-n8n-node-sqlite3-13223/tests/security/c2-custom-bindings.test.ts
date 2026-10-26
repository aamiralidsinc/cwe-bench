import path from 'path';
import { SqliteV1 } from '../../nodes/SqliteNode/v1/SqliteV1.node';
import { JsonObject, loadNodeParameters, makeContext } from '../support/n8n-params';
import { makeCaseDir, makeFile, removeCaseDir } from '../support/fixtures';

const FakeDatabase = require('../support/fake-better-sqlite3.js');
const records: Array<{ file: string; options: Record<string, unknown> }> = FakeDatabase.__records;

async function runV1(raw: JsonObject, items: JsonObject[]): Promise<void> {
  const node = new SqliteV1();
  const loaded = loadNodeParameters(node.description.properties, raw);
  const ctx = makeContext(loaded, items);
  await node.execute.call(ctx as never);
}

beforeEach(() => {
  records.length = 0;
});

describe('native bindings selection written as an expression', () => {
  test('a whole expression does not select the module that is loaded', async () => {
    const base = makeCaseDir();
    try {
      const chosen = makeFile(path.join(base, 'elsewhere', 'chosen.node'));
      let failed = false;
      try {
        await runV1(
          {
            db_path: path.join(base, 'test.sqlite'),
            query: 'SELECT 1',
            args: '{}',
            query_type: 'SELECT',
            spread: false,
            additionalOptions: { use_custom_bindings: '={{ $json.binding }}' },
          },
          [{ binding: chosen }],
        );
      } catch {
        failed = true;
      }
      const selected = records.map((entry) => entry.options.nativeBinding);
      expect(selected).not.toContain(chosen);
      expect(failed || selected.every((value) => value !== chosen)).toBe(true);
    } finally {
      removeCaseDir(base);
    }
  });
});
