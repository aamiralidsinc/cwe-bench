import { describe, expect, it } from 'vitest';
import { parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const schema = () => v.strictObject({ alpha: v.string() });

describe('a strict schema and an undeclared supplied name', () => {
  for (const name of [
    'toString',
    'valueOf',
    'hasOwnProperty',
    'constructor',
    '__proto__',
  ]) {
    it(`refuses the undeclared name "${name}" as an ordinary failure`, () => {
      const result = v.safeParse(
        schema(),
        parseObject(`{"alpha":"x","${name}":"y"}`)
      );
      expect(result.success).toBe(false);
      expect(result.issues?.length ?? 0).toBeGreaterThan(0);
    });
  }
});
