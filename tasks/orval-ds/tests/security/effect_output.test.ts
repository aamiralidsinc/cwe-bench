// Security: the alternative schema-output package reaches the same sinks.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const DEFAULT_KEY = 'a: 0, [' + ATTACK + ']: 0, b';

function effectCase(schema: Record<string, unknown>) {
  return generateCase({
    spec: specWithSchema(schema),
    output: { target: './gen/gen.ts', client: 'effect' },
  });
}

describe('generated schema modules for the alternative output', () => {
  it('a default string may not open an interpolation', () => {
    const value = 'a${' + ATTACK + '}b';
    const { dir, entry } = effectCase(
      objectSchema({ value: { type: 'string', default: value } }),
    );
    const out = evaluate(dir, entry, 'result = m.getThingResponseValueDefault;');
    expect(out.injected).toBe(false);
    // The value is carried as data: it still denotes exactly the described text.
    expect(out.result).toBe(value);
  });

  it('a key inside an object default may not become a computed property', () => {
    const { dir, entry } = effectCase(
      objectSchema({
        cfg: { type: 'object', default: { [DEFAULT_KEY]: 'v' } },
      }),
    );
    const out = evaluate(
      dir,
      entry,
      'result = Object.keys(m.getThingResponseCfgDefault);',
    );
    expect(out.injected).toBe(false);
    expect(out.result).toEqual([DEFAULT_KEY]);
  });
});
