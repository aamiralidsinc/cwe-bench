import { describe, expect, it } from 'vitest';
import * as v from '../support/product.ts';

describe('combining ordinary schemas', () => {
  it('merges ordinary fields provided by different schemas', () => {
    const result = v.safeParse(
      v.intersect([
        v.object({ alpha: v.string() }),
        v.object({ beta: v.string() }),
      ]),
      { alpha: 'x', beta: 'y' }
    );
    expect(result.success).toBe(true);
    expect(result.output).toEqual({ alpha: 'x', beta: 'y' });
  });

  it('accepts the same ordinary field with the same value in both schemas', () => {
    const result = v.safeParse(
      v.intersect([
        v.object({ alpha: v.string() }),
        v.object({ alpha: v.string() }),
      ]),
      { alpha: 'x' }
    );
    expect(result.success).toBe(true);
    expect(result.output).toEqual({ alpha: 'x' });
  });

  it('reports an issue when the same field has conflicting values', () => {
    const result = v.safeParse(
      v.intersect([
        v.object({ alpha: v.string() }),
        v.pipe(
          v.object({ alpha: v.string() }),
          v.transform((value) => ({ alpha: `${value.alpha}!` }))
        ),
      ]),
      { alpha: 'x' }
    );
    expect(result.success).toBe(false);
  });
});
