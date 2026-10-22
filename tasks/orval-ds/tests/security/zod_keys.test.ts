// Security: description-supplied names must stay keys of the generated object.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const KEY = 'a":(' + ATTACK + '),"b';
const DEFAULT_KEY = 'a: 0, [' + ATTACK + ']: 0, b';
const PARSED_KEYS = `result = Object.keys(m.GetThingResponse.parse({ ${JSON.stringify(
  KEY,
)}: 'v', ok: 'o' })).sort();`;

function zodCase(schema: Record<string, unknown>, output: Record<string, unknown> = {}) {
  return generateCase({
    spec: specWithSchema(schema),
    output: { target: './gen/gen.ts', client: 'zod', ...output },
  });
}

describe('generated validation module keys', () => {
  it('a property name may not break out of a double-quoted key', () => {
    const { dir, entry } = zodCase(
      objectSchema({ [KEY]: { type: 'string' }, ok: { type: 'string' } }),
    );
    const out = evaluate(dir, entry, PARSED_KEYS);
    expect(out.injected).toBe(false);
    // The name is carried as data: it is still exactly the described key.
    expect(out.result).toEqual([KEY, 'ok'].sort());
  });

  it('a property name may not break out in the compact output variant', () => {
    const { dir, entry } = zodCase(
      objectSchema({ [KEY]: { type: 'string' }, ok: { type: 'string' } }),
      { override: { zod: { variant: 'mini' } } },
    );
    const out = evaluate(dir, entry, PARSED_KEYS);
    expect(out.injected).toBe(false);
    // The name is carried as data: it is still exactly the described key.
    expect(out.result).toEqual([KEY, 'ok'].sort());
  });

  it('a property name may not break out after composition is merged', () => {
    const { dir, entry } = zodCase({
      allOf: [
        { type: 'object', properties: { [KEY]: { type: 'string' } } },
        { type: 'object', properties: { ok: { type: 'string' } } },
      ],
    });
    const out = evaluate(dir, entry, PARSED_KEYS);
    expect(out.injected).toBe(false);
    // The name is carried as data: it is still exactly the described key.
    expect(out.result).toEqual([KEY, 'ok'].sort());
  });

  it('a key inside an object default may not become a computed property', () => {
    const { dir, entry } = zodCase(
      objectSchema({
        cfg: { type: 'object', default: { [DEFAULT_KEY]: 'v' } },
      }),
    );
    const out = evaluate(
      dir,
      entry,
      'result = Object.keys(m.GetThingResponse.parse({}).cfg);',
    );
    expect(out.injected).toBe(false);
    expect(out.result).toEqual([DEFAULT_KEY]);
  });
});
