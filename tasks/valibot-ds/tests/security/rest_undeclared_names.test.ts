import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const schema = () => v.objectWithRest({ alpha: v.string() }, v.number());

describe('a catch-all schema rule and an undeclared supplied name', () => {
  for (const name of ['toString', 'valueOf', 'hasOwnProperty']) {
    it(`applies the catch-all rule to the supplied name "${name}"`, () => {
      const invalid = v.safeParse(
        schema(),
        parseObject(`{"alpha":"x","${name}":"not-a-number"}`)
      );
      expect(invalid.success).toBe(false);

      const valid = v.safeParse(
        schema(),
        parseObject(`{"alpha":"x","${name}":5}`)
      );
      expect(valid.success).toBe(true);
      expect(own(valid.output, name)).toBe(true);
      expect((valid.output as Record<string, unknown>)[name]).toBe(5);
    });
  }
});
