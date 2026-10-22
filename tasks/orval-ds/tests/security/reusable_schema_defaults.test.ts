// Security: shared/reusable schema output has its own default-emission path.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

describe('generated reusable schema modules', () => {
  it('a referenced property default may not open an interpolation', () => {
    const spec = specWithSchema(
      objectSchema({
        value: {
          $ref: '#/components/schemas/Inner',
          default: 'a${' + ATTACK + '}b',
        },
      }),
    );
    (spec.components as Record<string, unknown>).schemas = {
      Inner: { type: 'string' },
      Thing: objectSchema({
        value: {
          $ref: '#/components/schemas/Inner',
          default: 'a${' + ATTACK + '}b',
        },
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
    const out = evaluate(dir, entry, 'result = m.GetThingResponse.parse({}).value;');
    expect(out.injected).toBe(false);
    // The default is carried as data: it still denotes exactly the described text.
    expect(out.result).toBe('a${' + ATTACK + '}b');
  });
});
