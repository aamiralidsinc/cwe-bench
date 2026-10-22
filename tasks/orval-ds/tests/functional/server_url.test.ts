// Functional: description-derived base URLs still resolve.
import { describe, expect, it } from 'vitest';

import { evaluate, generateCase, simpleSpec } from '../support/harness';

function serverUrl(
  servers: unknown[],
  baseUrl: Record<string, unknown>,
): unknown {
  const spec = simpleSpec('/pets');
  spec.servers = servers;
  const { dir, entry } = generateCase({
    spec,
    output: { target: './gen/gen.ts', client: 'fetch', baseUrl },
  });
  const result = evaluate(dir, entry, 'result = m.getGetThingUrl();');
  expect(result.error).toBe('');
  return result.result;
}

describe('base URL resolution', () => {
  it('server variables are substituted from their defaults', () => {
    expect(
      serverUrl(
        [{ url: 'http://{env}.example.com', variables: { env: { default: 'prod' } } }],
        { getBaseUrlFromSpecification: true },
      ),
    ).toBe('http://prod.example.com/pets');
  });

  it('configured server variable values still win', () => {
    expect(
      serverUrl(
        [{ url: 'http://{env}.example.com', variables: { env: { default: 'prod' } } }],
        { getBaseUrlFromSpecification: true, variables: { env: 'staging' } },
      ),
    ).toBe('http://staging.example.com/pets');
  });

  it('quotes in a plain server URL are preserved', () => {
    expect(
      serverUrl([{ url: `https://api.example.com/o'neil/say"hi"` }], {
        getBaseUrlFromSpecification: true,
      }),
    ).toBe(`https://api.example.com/o'neil/say"hi"/pets`);
  });

  it('quotes in a server variable default are preserved', () => {
    expect(
      serverUrl(
        [
          {
            url: 'https://api.example.com/{tenant}',
            variables: { tenant: { default: `o'neil"s"` } },
          },
        ],
        { getBaseUrlFromSpecification: true },
      ),
    ).toBe(`https://api.example.com/o'neil"s"/pets`);
  });

  it('a plain server URL still prefixes the route', () => {
    expect(
      serverUrl([{ url: 'https://api.example.com/v1' }], {
        getBaseUrlFromSpecification: true,
      }),
    ).toBe('https://api.example.com/v1/pets');
  });
});
