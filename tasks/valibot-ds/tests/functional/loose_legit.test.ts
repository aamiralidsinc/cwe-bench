import { describe, expect, it } from 'vitest';
import { own, parseObject } from '../support/helpers.ts';
import * as v from '../support/product.ts';

describe('a pass-through schema in ordinary use', () => {
  const schema = () => v.looseObject({ alpha: v.string() });

  it('still keeps an ordinary undeclared field', () => {
    const result = v.safeParse(schema(), { alpha: 'x', beta: 'y' });
    expect(result.success).toBe(true);
    expect(own(result.output, 'beta')).toBe(true);
    expect((result.output as Record<string, unknown>).beta).toBe('y');
  });

  it('still requires a declared field', () => {
    const result = v.safeParse(schema(), {});
    expect(result.success).toBe(false);
  });

  it('binds a declared field whose name is inherited by every object', () => {
    const result = v.safeParse(
      v.looseObject({ toString: v.string() }),
      parseObject('{"toString":"x"}')
    );
    expect(result.success).toBe(true);
    expect(own(result.output, 'toString')).toBe(true);
    expect((result.output as Record<string, unknown>).toString).toBe('x');
  });

  it('keeps the deliberate exclusion of prototype-mutating names', () => {
    const result = v.safeParse(
      schema(),
      parseObject('{"alpha":"x","__proto__":"y","constructor":"z"}')
    );
    expect(result.success).toBe(true);
    expect(own(result.output, '__proto__')).toBe(false);
    expect(own(result.output, 'constructor')).toBe(false);
  });
});
