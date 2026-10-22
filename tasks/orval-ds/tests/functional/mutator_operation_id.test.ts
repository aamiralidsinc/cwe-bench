// Functional: custom mutators keep receiving the described operation identity.
import { describe, expect, it } from 'vitest';

import { evaluate, generateCase } from '../support/harness';

const OPERATION_ID = 'List Pets v2';

const RECORDER = `
export const useCustom = (options: any, _second?: any, _third?: any) => {
  (globalThis as any).__MUTATOR_ARG = _third;
  return options;
};
`;

describe('mutator operation metadata', () => {
  it('a query mutator receives the described operation id and route', () => {
    const { dir, entry } = generateCase({
      spec: {
        openapi: '3.1.0',
        info: { title: 'verifier', version: '1.0.0' },
        paths: {
          '/things': {
            get: {
              operationId: OPERATION_ID,
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
    expect(out.error).toBe('');
    const metadata = out.result as Record<string, unknown>;
    expect(metadata.operationId).toBe(OPERATION_ID);
    expect(metadata.url).toBe('/things');
  });

  it('a mutation mutator receives the described operation id', () => {
    const { dir, entry } = generateCase({
      spec: {
        openapi: '3.1.0',
        info: { title: 'verifier', version: '1.0.0' },
        paths: {
          '/things': {
            post: {
              operationId: 'Create Pets v2',
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
    expect(out.error).toBe('');
    expect((out.result as Record<string, unknown>).operationId).toBe(
      'Create Pets v2',
    );
  });
});
