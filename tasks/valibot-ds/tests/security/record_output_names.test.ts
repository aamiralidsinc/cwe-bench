import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const collection = () => v.record(v.string(), v.number());

describe('the output of a validated collection', () => {
  for (const name of ['toString', 'valueOf', 'hasOwnProperty']) {
    it(`keeps the accepted entry named "${name}"`, () => {
      const result = v.safeParse(
        collection(),
        parseObject(`{"alpha":1,"${name}":5}`)
      );
      expect(result.success).toBe(true);
      expect(own(result.output, name)).toBe(true);
      expect((result.output as Record<string, unknown>)[name]).toBe(5);
    });
  }
});
