import { describe, expect, it } from 'vitest';
import { flattenIssues, own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const collection = () => v.record(v.string(), v.number());
const nested = (flat: ReturnType<typeof flattenIssues>) =>
  flat.nested as Record<string, string[]>;

describe('flattening messages of a validated collection', () => {
  for (const name of ['toString', 'valueOf', 'hasOwnProperty']) {
    it(`keeps the message under the supplied name "${name}"`, () => {
      const result = v.safeParse(
        collection(),
        parseObject(`{"alpha":1,"${name}":"x"}`)
      );
      expect(result.success).toBe(false);

      const flat = flattenIssues(result.issues!);
      expect(own(flat.nested, name)).toBe(true);
      expect(nested(flat)[name]).toEqual(
        result.issues!.map((issue) => issue.message)
      );
    });
  }

  it('accumulates several messages under one supplied name', () => {
    const first = v.safeParse(collection(), parseObject('{"toString":"x"}'));
    const second = v.safeParse(collection(), parseObject('{"toString":"y"}'));
    expect(first.success).toBe(false);
    expect(second.success).toBe(false);

    const flat = flattenIssues(first.issues!, second.issues!);
    expect(own(flat.nested, 'toString')).toBe(true);
    expect(nested(flat)['toString']).toEqual([
      first.issues![0].message,
      second.issues![0].message,
    ]);
  });
});
