// Security: description values that reach generated validation modules must stay data.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const BACKTICK = 'a`+(' + ATTACK + ')+`b';
const INTERPOLATION = 'a${' + ATTACK + '}b';
const PARSED_VALUE = 'result = m.GetThingResponse.parse({}).value;';

function zodCase(schema: Record<string, unknown>) {
  return generateCase({
    spec: specWithSchema(schema),
    output: { target: './gen/gen.ts', client: 'zod' },
  });
}

describe('generated validation modules', () => {
  it('a default string may not break out of its template literal', () => {
    const { dir, entry } = zodCase(
      objectSchema({ value: { type: 'string', default: BACKTICK } }),
    );
    const out = evaluate(dir, entry, PARSED_VALUE);
    expect(out.injected).toBe(false);
    // The default is carried as data: it still denotes exactly the described text.
    expect(out.result).toEqual(BACKTICK);
  });

  it('a default string may not open an interpolation', () => {
    const { dir, entry } = zodCase(
      objectSchema({ value: { type: 'string', default: INTERPOLATION } }),
    );
    const out = evaluate(dir, entry, PARSED_VALUE);
    expect(out.injected).toBe(false);
    // The default is carried as data: it still denotes exactly the described text.
    expect(out.result).toEqual(INTERPOLATION);
  });

  it('an array default may not carry executable item text', () => {
    const { dir, entry } = zodCase(
      objectSchema({
        value: {
          type: 'array',
          items: { type: 'string' },
          default: ['safe', BACKTICK],
        },
      }),
    );
    const out = evaluate(dir, entry, PARSED_VALUE);
    expect(out.injected).toBe(false);
    // The default is carried as data: it still denotes exactly the described text.
    expect(out.result).toEqual(['safe', BACKTICK]);
  });

  it('an enum-typed default may not carry executable text', () => {
    const { dir, entry } = zodCase(
      objectSchema({
        value: {
          type: 'string',
          enum: ['safe', INTERPOLATION],
          default: INTERPOLATION,
        },
      }),
    );
    const out = evaluate(dir, entry, PARSED_VALUE);
    expect(out.injected).toBe(false);
    // The default is carried as data: it still denotes exactly the described text.
    expect(out.result).toEqual(INTERPOLATION);
  });
});
