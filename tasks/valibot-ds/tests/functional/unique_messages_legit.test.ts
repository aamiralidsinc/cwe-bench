import { describe, expect, it } from 'vitest';
import { own } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const collection = () => v.record(v.string(), v.number());

describe('one message per path in ordinary use', () => {
  it('keeps the first message for a repeated ordinary path', () => {
    const first = v.safeParse(collection(), { alpha: 'x' });
    const second = v.safeParse(collection(), { alpha: 'y' });
    expect(first.success).toBe(false);
    expect(second.success).toBe(false);

    const messages = v.uniqueMessages([
      ...first.issues!,
      ...second.issues!,
    ] as [never, ...never[]]);
    expect(messages.alpha).toBe(first.issues![0].message);
    expect(Object.keys(messages)).toEqual(['alpha']);
  });

  it('keeps one message for each distinct ordinary path', () => {
    const result = v.safeParse(collection(), { alpha: 'x', beta: 'y' });
    expect(result.success).toBe(false);

    const messages = v.uniqueMessages(result.issues!);
    expect(own(messages, 'alpha')).toBe(true);
    expect(own(messages, 'beta')).toBe(true);
    expect(Object.keys(messages).sort()).toEqual(['alpha', 'beta']);
  });
});
