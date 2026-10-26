import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const collection = () => v.record(v.string(), v.number());

describe('a validated collection in ordinary use', () => {
  it('returns every accepted entry', () => {
    const result = v.safeParse(collection(), { alpha: 1, beta: 2 });
    expect(result.success).toBe(true);
    expect(result.output).toEqual({ alpha: 1, beta: 2 });
  });

  it('reports an invalid entry value', () => {
    const result = v.safeParse(collection(), { alpha: 'x' });
    expect(result.success).toBe(false);
  });

  it('keeps the first value when transformed entry names collide', () => {
    const result = v.safeParse(
      v.record(v.pipe(v.string(), v.toUpperCase()), v.number()),
      parseObject('{"a":1,"A":2}')
    );
    expect(result.success).toBe(true);
    expect(own(result.output, 'A')).toBe(true);
    expect((result.output as Record<string, unknown>).A).toBe(1);
  });
});
