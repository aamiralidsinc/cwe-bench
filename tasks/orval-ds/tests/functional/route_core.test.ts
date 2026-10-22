// Functional: ordinary route handling must be unchanged.
import { describe, expect, it } from 'vitest';

import { evaluate, generateCase, simpleSpec } from '../support/harness';

const PARAM = [
  { name: 'petId', in: 'path', required: true, schema: { type: 'string' } },
];

function fetchUrl(spec: Record<string, unknown>, operation: string) {
  const { dir, entry } = generateCase({
    spec,
    output: { target: './gen/gen.ts', client: 'fetch' },
  });
  const result = evaluate(dir, entry, `result = m.${operation}('abc');`);
  expect(result.error).toBe('');
  return result.result;
}

describe('request URL construction', () => {
  it('path placeholders still interpolate the caller value', () => {
    expect(fetchUrl(simpleSpec('/pets/{petId}', 'getPets', PARAM), 'getGetPetsUrl')).toBe(
      '/pets/abc',
    );
  });

  it('a dollar sign not followed by a brace stays literal', () => {
    expect(fetchUrl(simpleSpec('/price$/list'), 'getGetThingUrl')).toBe(
      '/price$/list',
    );
  });

  it('quotes in static route text are preserved', () => {
    expect(
      fetchUrl(
        simpleSpec(`/pets/o'neil/say"hi"/{petId}`, 'getPets', PARAM),
        'getGetPetsUrl',
      ),
    ).toBe(`/pets/o'neil/say"hi"/abc`);
  });

  it('dots and dashes in static route text are preserved', () => {
    expect(
      fetchUrl(
        simpleSpec('/v1/pet-store/all.items/{petId}', 'getPets', PARAM),
        'getGetPetsUrl',
      ),
    ).toBe('/v1/pet-store/all.items/abc');
  });
});
