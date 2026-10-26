import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

describe('a strict schema in ordinary use', () => {
  it('still refuses an ordinary undeclared field', () => {
    const result = v.safeParse(v.strictObject({ alpha: v.string() }), {
      alpha: 'x',
      beta: 'y',
    });
    expect(result.success).toBe(false);
  });

  it('still requires a declared field', () => {
    const result = v.safeParse(v.strictObject({ alpha: v.string() }), {});
    expect(result.success).toBe(false);
  });

  it('binds a declared field whose name is inherited by every object', () => {
    const result = v.safeParse(
      v.strictObject({ toString: v.string() }),
      parseObject('{"toString":"x"}')
    );
    expect(result.success).toBe(true);
    expect(own(result.output, 'toString')).toBe(true);
    expect((result.output as Record<string, unknown>).toString).toBe('x');
  });
});
