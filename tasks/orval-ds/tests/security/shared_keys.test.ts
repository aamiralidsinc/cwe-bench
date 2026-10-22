// Security: the shared name helper feeds generated mock objects as well as types.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const KEY = "x':(" + ATTACK + "),'y";

describe('generated mock objects', () => {
  it('a property name may not break out of a single-quoted key', () => {
    const { dir } = generateCase({
      spec: specWithSchema(objectSchema({ [KEY]: { type: 'string' } })),
      output: {
        target: './api/gen.ts',
        client: 'fetch',
        mode: 'split',
        mock: true,
      },
      entry: './api/gen.faker.ts',
    });
    const result = evaluate(
      dir,
      './api/gen.faker.ts',
      'result = Object.keys(m.getGetThingResponseMock());',
    );
    expect(result.injected).toBe(false);
    // The name is carried as data: the mock has exactly one key, the described name.
    expect(result.result).toEqual([KEY]);
  });
});
