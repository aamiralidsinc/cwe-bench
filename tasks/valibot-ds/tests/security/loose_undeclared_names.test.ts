import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const schema = () => v.looseObject({ alpha: v.string() });

describe('a pass-through schema and an undeclared supplied name', () => {
  for (const name of ['toString', 'valueOf', 'hasOwnProperty']) {
    it(`keeps the undeclared supplied name "${name}" in the output`, () => {
      const result = v.safeParse(
        schema(),
        parseObject(`{"alpha":"x","${name}":"y"}`)
      );
      expect(result.success).toBe(true);
      expect(own(result.output, name)).toBe(true);
      expect((result.output as Record<string, unknown>)[name]).toBe('y');
    });
  }
});
