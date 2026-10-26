import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

describe('a catch-all schema in ordinary use', () => {
  const schema = () => v.objectWithRest({ alpha: v.string() }, v.number());

  it('still applies the catch-all rule to an ordinary undeclared field', () => {
    const invalid = v.safeParse(schema(), { alpha: 'x', beta: 'nope' });
    expect(invalid.success).toBe(false);

    const valid = v.safeParse(schema(), { alpha: 'x', beta: 5 });
    expect(valid.success).toBe(true);
    expect(own(valid.output, 'beta')).toBe(true);
    expect((valid.output as Record<string, unknown>).beta).toBe(5);
  });

  it('still requires a declared field', () => {
    const result = v.safeParse(schema(), {});
    expect(result.success).toBe(false);
  });

  it('binds a declared field whose name is inherited by every object', () => {
    const result = v.safeParse(
      v.objectWithRest({ toString: v.string() }, v.number()),
      parseObject('{"toString":"x"}')
    );
    expect(result.success).toBe(true);
    expect(own(result.output, 'toString')).toBe(true);
    expect((result.output as Record<string, unknown>).toString).toBe('x');
  });

  it('keeps the deliberate exclusion of prototype-mutating names', () => {
    const result = v.safeParse(
      v.objectWithRest({ alpha: v.string() }, v.any()),
      parseObject('{"alpha":"x","__proto__":{"polluted":true}}')
    );
    expect(result.success).toBe(true);
    expect(own(result.output, '__proto__')).toBe(false);
  });
});
