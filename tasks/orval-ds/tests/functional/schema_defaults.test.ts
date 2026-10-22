// Functional: description values must survive generation exactly.
import { describe, expect, it } from 'vitest';

import {
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const SPECIAL = "C:\\logs\\";
const QUOTED = 'say "hi" from C:\\temp\\';
const NAME = "it's a`b${c}";

describe('generated validation schema values', () => {
  it('special characters in a string default round-trip', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({ value: { type: 'string', default: SPECIAL } }),
      ),
      output: { target: './gen/gen.ts', client: 'zod' },
    });
    const body = `
const parsed = m.GetThingResponse.parse({});
result = parsed.value;
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toBe(SPECIAL);
  });

  it('array, enum and non-string defaults keep their values', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({
          tags: { type: 'array', items: { type: 'string' }, default: ['a', 'b'] },
          kind: { type: 'string', enum: ['x', 'y'], default: 'y' },
          count: { type: 'number', default: 7 },
          enabled: { type: 'boolean', default: true },
          nothing: { type: 'string', nullable: true, default: null },
        }),
      ),
      output: { target: './gen/gen.ts', client: 'zod' },
    });
    const body = `
const parsed = m.GetThingResponse.parse({});
result = {
  tags: parsed.tags,
  kind: parsed.kind,
  count: parsed.count,
  enabled: parsed.enabled,
  nothing: parsed.nothing,
};
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toEqual({
      tags: ['a', 'b'],
      kind: 'y',
      count: 7,
      enabled: true,
      nothing: null,
    });
  });

  it('quotes in string, array and enum defaults round-trip', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({
          value: { type: 'string', default: QUOTED },
          tags: { type: 'array', items: { type: 'string' }, default: [QUOTED, 'b'] },
          kind: { type: 'string', enum: ['x', QUOTED], default: QUOTED },
        }),
      ),
      output: { target: './gen/gen.ts', client: 'zod' },
    });
    const body = `
const parsed = m.GetThingResponse.parse({});
result = { value: parsed.value, tags: parsed.tags, kind: parsed.kind };
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toEqual({ value: QUOTED, tags: [QUOTED, 'b'], kind: QUOTED });
  });

  it('a referenced property default with quotes round-trips', () => {
    const spec = specWithSchema(objectSchema({}));
    (spec.components as Record<string, unknown>).schemas = {
      Inner: { type: 'string' },
      Thing: objectSchema({
        value: { $ref: '#/components/schemas/Inner', default: QUOTED },
      }),
    };
    const { dir, entry } = generateCase({
      spec,
      output: {
        target: './gen/gen.ts',
        client: 'zod',
        override: { zod: { generateReusableSchemas: true } },
      },
    });
    const out = evaluate(
      dir,
      entry,
      'result = m.GetThingResponse.parse({}).value;',
    );
    expect(out.error).toBe('');
    expect(out.result).toBe(QUOTED);
  });

  it('an object default keeps its keys as data keys', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({ cfg: { type: 'object', default: { cfgKey: 'v' } } }),
      ),
      output: { target: './gen/gen.ts', client: 'zod' },
    });
    const body = `
const parsed = m.GetThingResponse.parse({});
result = parsed.cfg.cfgKey;
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toBe('v');
  });

  it('a property name with special characters stays a data key', () => {
    const name = 'a`b${c}';
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({ [name]: { type: 'string' } }),
      ),
      output: { target: './gen/gen.ts', client: 'zod' },
    });
    const body = `
const parsed = m.GetThingResponse.parse({ ${JSON.stringify(name)}: 'v' });
result = Object.keys(parsed);
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toContain(name);
  });

  it('a property name with quotes keeps its exact name in every output form', () => {
    const cases: [string, Record<string, unknown>, Record<string, unknown>][] = [
      ['standard', objectSchema({ [NAME]: { type: 'string' }, ok: { type: 'string' } }), {}],
      [
        'compact',
        objectSchema({ [NAME]: { type: 'string' }, ok: { type: 'string' } }),
        { override: { zod: { variant: 'mini' } } },
      ],
      [
        'merged',
        {
          allOf: [
            { type: 'object', properties: { [NAME]: { type: 'string' } } },
            { type: 'object', properties: { ok: { type: 'string' } } },
          ],
        },
        {},
      ],
    ];
    const body = `
const parsed = m.GetThingResponse.parse({ ${JSON.stringify(NAME)}: 'v', ok: 'o' });
result = Object.keys(parsed).sort();
`;
    for (const [label, schema, extra] of cases) {
      const { dir, entry } = generateCase({
        spec: specWithSchema(schema),
        output: { target: './gen/gen.ts', client: 'zod', ...extra },
      });
      const out = evaluate(dir, entry, body);
      expect(out.error, label).toBe('');
      expect(out.result, label).toEqual([NAME, 'ok'].sort());
    }
  });
});
