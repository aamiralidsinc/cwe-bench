// Security: the operation identifier is passed to custom mutators as generated data.
import { describe, expect, it } from 'vitest';

import { evaluate, generateCase } from '../support/harness';

const OPERATION_ID = "getThing', __x: (globalThis.__PWNED=true), __z: '";
const MUTATION_ID = "createThing', __x: (globalThis.__PWNED=true), __z: '";

const RECORDER = `
export const useCustom = (options: any, _second?: any, _third?: any) => {
  (globalThis as any).__MUTATOR_ARG = _third;
  return options;
};
`;

function readOnlySpec(operationId: string): Record<string, unknown> {
  return {
    openapi: '3.1.0',
    info: { title: 'verifier', version: '1.0.0' },
    paths: {
      '/things': {
        get: {
          operationId,
          responses: {
            200: {
              description: 'ok',
              content: { 'application/json': { schema: { type: 'object' } } },
            },
          },
        },
      },
    },
  };
}

describe('generated mutator metadata', () => {
  it('a query operation id may not become part of the surrounding object', () => {
    const { dir, entry } = generateCase({
      spec: readOnlySpec(OPERATION_ID),
      files: { 'mutator.ts': RECORDER },
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: {
          query: {
            queryOptions: {
              path: './mutator.ts',
              name: 'useCustom',
              hasSecondArg: true,
              hasThirdArg: true,
            },
          },
        },
      },
    });

    const body = `
const name = Object.keys(m).find((key) => key.endsWith('QueryOptions'));
m[name]({});
result = (globalThis as any).__MUTATOR_ARG;
`;
    const out = evaluate(dir, entry, body);
    expect(out.injected).toBe(false);
    // The identifier is carried as data: the mutator receives exactly the described text.
    expect((out.result as Record<string, unknown> | undefined)?.operationId).toBe(
      OPERATION_ID,
    );
  });

  it('a mutation operation id may not become part of the surrounding object', () => {
    const { dir, entry } = generateCase({
      spec: {
        openapi: '3.1.0',
        info: { title: 'verifier', version: '1.0.0' },
        paths: {
          '/things': {
            post: {
              operationId: MUTATION_ID,
              requestBody: {
                required: true,
                content: {
                  'application/json': { schema: { type: 'object' } },
                },
              },
              responses: {
                200: {
                  description: 'ok',
                  content: {
                    'application/json': { schema: { type: 'object' } },
                  },
                },
              },
            },
          },
        },
      },
      files: { 'mutator.ts': RECORDER },
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: {
          query: {
            mutationOptions: {
              path: './mutator.ts',
              name: 'useCustom',
              hasSecondArg: true,
              hasThirdArg: true,
            },
          },
        },
      },
    });

    const body = `
const name = Object.keys(m).find((key) => key.endsWith('MutationOptions'));
m[name]({});
result = (globalThis as any).__MUTATOR_ARG;
`;
    const out = evaluate(dir, entry, body);
    expect(out.injected).toBe(false);
    expect((out.result as Record<string, unknown> | undefined)?.operationId).toBe(
      MUTATION_ID,
    );
  });
});
