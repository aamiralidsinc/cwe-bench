import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

describe('keeping one message per path', () => {
  for (const name of ['toString', 'valueOf', 'hasOwnProperty']) {
    it(`keeps the message for the supplied name "${name}"`, () => {
      const result = v.safeParse(
        v.record(v.string(), v.number()),
        parseObject(`{"${name}":"x"}`)
      );
      expect(result.success).toBe(false);

      const messages = v.uniqueMessages(result.issues!);
      expect(own(messages, name)).toBe(true);
      expect(messages[name]).toBe(result.issues![0].message);
    });
  }
});
