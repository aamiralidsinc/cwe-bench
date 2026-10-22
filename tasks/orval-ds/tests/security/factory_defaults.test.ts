// Security: mock factory helpers carry description defaults into source.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const DATE = "2020-01-01'), __m: (" + ATTACK + "), __x: new Date('";

describe('generated factory helpers', () => {
  it('a date default may not break out of its Date literal', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({ when: { type: 'string', format: 'date', default: DATE } }),
      ),
      output: {
        target: './gen/gen.ts',
        client: 'fetch',
        factoryMethods: { mode: 'single' },
        override: { useDates: true },
      },
    });
    expect(evaluate(dir, entry, 'm.createThing();').injected).toBe(false);
  });
});
