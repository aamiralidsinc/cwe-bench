import fs from 'fs';
import path from 'path';
import { SqliteV1 } from '../../nodes/SqliteNode/v1/SqliteV1.node';
import { JsonObject, loadNodeParameters, makeContext } from '../support/n8n-params';
import { makeCaseDir, removeCaseDir } from '../support/fixtures';

const FakeDatabase = require('../support/fake-better-sqlite3.js');
const records: Array<{ file: string; options: Record<string, unknown> }> = FakeDatabase.__records;

const baseParams: JsonObject = {
  query: 'SELECT 1',
  args: '{}',
  query_type: 'SELECT',
  spread: false,
  additionalOptions: {},
};

async function runV1(raw: JsonObject, items: JsonObject[]): Promise<void> {
  const node = new SqliteV1();
  const loaded = loadNodeParameters(node.description.properties, raw);
  const ctx = makeContext(loaded, items);
  await node.execute.call(ctx as never);
}

/** A refusal is a valid outcome; the assertions are about which file the product touched. */
async function attempt(work: () => Promise<void>): Promise<void> {
  try {
    await work();
  } catch {
    /* a controlled refusal is acceptable */
  }
}

function recordedFiles(): string[] {
  return records.map((entry) => path.resolve(entry.file));
}

beforeEach(() => {
  records.length = 0;
});

describe('database path written as an expression', () => {
  test('a whole expression does not select the opened file', async () => {
    const base = makeCaseDir();
    try {
      const outside = path.join(base, 'elsewhere', 'chosen.sqlite');
      await attempt(() =>
        runV1({ ...baseParams, db_path: '={{ $json.db }}' }, [{ db: outside }]),
      );
      expect(fs.existsSync(path.dirname(outside))).toBe(false);
      expect(recordedFiles()).not.toContain(path.resolve(outside));
    } finally {
      removeCaseDir(base);
    }
  });

  test('a fragment of a larger string does not change the selected file', async () => {
    const base = makeCaseDir();
    try {
      const safe = path.join(base, 'safe');
      const chosen = path.join(safe, 'chosen.sqlite');
      await attempt(() =>
        runV1(
          { ...baseParams, db_path: `=${safe}/{{ $json.name }}.sqlite` },
          [{ name: 'chosen' }],
        ),
      );
      expect(recordedFiles()).not.toContain(path.resolve(chosen));
      expect(fs.existsSync(chosen)).toBe(false);
    } finally {
      removeCaseDir(base);
    }
  });

  test('each item cannot choose its own file', async () => {
    const base = makeCaseDir();
    try {
      const first = path.join(base, 'first', 'one.sqlite');
      const second = path.join(base, 'second', 'two.sqlite');
      await attempt(() =>
        runV1({ ...baseParams, db_path: '={{ $json.db }}' }, [{ db: first }, { db: second }]),
      );
      const opened = recordedFiles();
      expect(opened).not.toContain(path.resolve(first));
      expect(opened).not.toContain(path.resolve(second));
      expect(fs.existsSync(path.dirname(first))).toBe(false);
      expect(fs.existsSync(path.dirname(second))).toBe(false);
    } finally {
      removeCaseDir(base);
    }
  });

  test('a value that is not used creates nothing on disk', async () => {
    const base = makeCaseDir();
    try {
      const outside = path.join(base, 'outside', 'deep', 'chosen.sqlite');
      let failed = false;
      try {
        await runV1({ ...baseParams, db_path: '={{ $json.db }}' }, [{ db: outside }]);
      } catch {
        failed = true;
      }
      // Either outcome is acceptable, but the directory the expression selected must not exist.
      expect(failed || fs.existsSync(path.dirname(outside)) === false).toBe(true);
      expect(fs.existsSync(path.join(base, 'outside'))).toBe(false);
    } finally {
      removeCaseDir(base);
    }
  });
});
