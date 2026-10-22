// Functional: the alternative schema output still emits usable defaults.
import { describe, expect, it } from 'vitest';

import {
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

describe('alternative schema output', () => {
  it('a string default is exported with its exact value', () => {
    const value = 'C:\\logs\\';
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({ value: { type: 'string', default: value } }),
      ),
      output: { target: './gen/gen.ts', client: 'effect' },
    });
    const out = evaluate(dir, entry, 'result = m.getThingResponseValueDefault;');
    expect(out.error).toBe('');
    expect(out.result).toBe(value);
  });

  it('string and array defaults with quotes keep their exact values', () => {
    const value = 'say "hi" from C:\\temp\\';
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({
          value: { type: 'string', default: value },
          tags: { type: 'array', items: { type: 'string' }, default: [value, 'b'] },
        }),
      ),
      output: { target: './gen/gen.ts', client: 'effect' },
    });
    const out = evaluate(
      dir,
      entry,
      'result = [m.getThingResponseValueDefault, m.getThingResponseTagsDefault];',
    );
    expect(out.error).toBe('');
    expect(out.result).toEqual([value, [value, 'b']]);
  });
});
