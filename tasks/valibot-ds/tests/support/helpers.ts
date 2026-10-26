import * as v from './product.ts';

/** Whether `key` is an own property of `object` (never resolved through inheritance). */
export function own(object: unknown, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(object, key);
}

/**
 * Builds an object from JSON text. Unlike an object literal, JSON text can give
 * the result an own property with any name at all.
 */
export function parseObject(text: string): Record<string, unknown> {
  return JSON.parse(text) as Record<string, unknown>;
}

/** Calls the flattening helper with one or more issue lists. */
export function flattenIssues(...groups: readonly unknown[][]) {
  return v.flatten(groups.flat() as [never, ...never[]]);
}
