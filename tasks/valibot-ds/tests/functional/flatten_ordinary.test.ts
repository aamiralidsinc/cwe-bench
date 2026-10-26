import { describe, expect, it } from 'vitest';
import { flattenIssues } from '../support/helpers.ts';
import * as v from '../support/product.ts';

const nested = (flat: ReturnType<typeof flattenIssues>) =>
  flat.nested as Record<string, string[]>;

describe('flattening ordinary messages', () => {
  it('accumulates several messages for the same ordinary field', () => {
    const first = v.safeParse(
      v.record(v.string(), v.number()),
      { alpha: 'x' }
    );
    const second = v.safeParse(
      v.record(v.string(), v.number()),
      { alpha: 'y' }
    );
    expect(first.success).toBe(false);
    expect(second.success).toBe(false);

    const flat = flattenIssues(first.issues!, second.issues!);
    expect(nested(flat).alpha).toEqual([
      first.issues![0].message,
      second.issues![0].message,
    ]);
  });

  it('puts messages without a path in the root group', () => {
    const result = v.safeParse(v.number(), 'x');
    expect(result.success).toBe(false);
    const flat = flattenIssues(result.issues!);
    expect(flat.root).toEqual([result.issues![0].message]);
  });

  it('puts messages for paths that are not names in the other group', () => {
    const result = v.safeParse(
      v.map(v.any(), v.number()),
      new Map([[Symbol('key'), 'x']])
    );
    expect(result.success).toBe(false);
    const flat = flattenIssues(result.issues!);
    expect(flat.other).toEqual([result.issues![0].message]);
  });

  it('renders nested ordinary paths with their dot path', () => {
    const result = v.safeParse(
      v.object({ outer: v.object({ inner: v.number() }) }),
      { outer: { inner: 'x' } }
    );
    expect(result.success).toBe(false);
    const flat = flattenIssues(result.issues!);
    expect(nested(flat)['outer.inner']).toEqual([result.issues![0].message]);
  });
});
