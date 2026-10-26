import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const schema = (name: string) =>
  v.intersect([v.object({ alpha: v.string() }), v.object({ [name]: v.string() })]);

describe('combining two schemas over a supplied name', () => {
  for (const name of [
    'toString',
    'valueOf',
    'hasOwnProperty',
    'constructor',
  ]) {
    it(`merges the supplied name "${name}" like an ordinary field`, () => {
      const result = v.safeParse(
        schema(name),
        parseObject(`{"alpha":"x","${name}":"y"}`)
      );
      expect(result.success).toBe(true);
      const output = result.output as Record<string, unknown>;
      expect(output.alpha).toBe('x');
      expect(own(output, name)).toBe(true);
      expect(output[name]).toBe('y');
    });
  }
});
