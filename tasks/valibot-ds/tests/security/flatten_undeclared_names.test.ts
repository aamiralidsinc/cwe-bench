import { describe, expect, it } from 'vitest';
import { flattenIssues, own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const schema = () => v.strictObject({ alpha: v.string() });
const nested = (flat: ReturnType<typeof flattenIssues>) =>
  flat.nested as Record<string, string[]>;

describe('flattening the refusal of an undeclared supplied name', () => {
  for (const name of ['toString', 'constructor', '__proto__']) {
    it(`keeps the message under the refused name "${name}"`, () => {
      const result = v.safeParse(
        schema(),
        parseObject(`{"alpha":"x","${name}":"y"}`)
      );
      // The strict schema must refuse the undeclared name.
      expect(result.success).toBe(false);

      const flat = flattenIssues(result.issues!);
      expect(own(flat.nested, name)).toBe(true);
      expect(nested(flat)[name]).toEqual(
        result.issues!.map((issue) => issue.message)
      );
      // The messages must stay ordinary data, not become the result's prototype.
      expect(Array.isArray(Object.getPrototypeOf(flat.nested))).toBe(false);
    });
  }
});
