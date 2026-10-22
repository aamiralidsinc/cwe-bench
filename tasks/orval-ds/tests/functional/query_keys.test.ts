// Functional: cache keys and invalidation prefixes still match.
import { describe, expect, it } from 'vitest';

import { evaluate, generateCase, simpleSpec } from '../support/harness';

const PARAM = [
  { name: 'thingId', in: 'path', required: true, schema: { type: 'string' } },
];

describe('query cache keys', () => {
  it('a split query key still carries the route segments', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/{thingId}', 'getThing', PARAM),
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: { query: { shouldSplitQueryKey: true } },
      },
    });
    const out = evaluate(dir, entry, "result = m.getGetThingQueryKey('id');");
    expect(out.error).toBe('');
    expect(out.result).toEqual(['things', 'id']);
  });

  it('a split query key keeps quotes in a static segment', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/say"hi"/{thingId}', 'getThing', PARAM),
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: { query: { shouldSplitQueryKey: true } },
      },
    });
    const out = evaluate(dir, entry, "result = m.getGetThingQueryKey('id');");
    expect(out.error).toBe('');
    expect(out.result).toEqual(['things', 'say"hi"', 'id']);
  });

  it('a mutation invalidation prefix still matches its route', () => {
    const spec = simpleSpec('/people/{personId}', 'getPerson', [
      { name: 'personId', in: 'path', required: true, schema: { type: 'string' } },
    ]);
    spec.paths['/people'] = {
      post: { operationId: 'createPerson', responses: { 200: { description: 'ok' } } },
    };
    const { dir, entry } = generateCase({
      spec,
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: {
          query: {
            mutationInvalidates: [
              { onMutations: ['createPerson'], invalidates: ['getPerson'] },
            ],
          },
        },
      },
    });
    const body = `
let matched: unknown = null;
const options = m.getCreatePersonMutationOptions({
  invalidateQueries(arg: any) {
    if (arg && typeof arg.predicate === 'function') {
      matched = arg.predicate({ queryKey: ['/people/abc'] });
    }
  },
});
options.onSuccess({}, undefined, undefined);
result = matched;
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toBe(true);
  });

  it('a mutation invalidation prefix keeps quotes in its route', () => {
    const spec = simpleSpec('/people/say"hi"/{personId}', 'getPerson', [
      { name: 'personId', in: 'path', required: true, schema: { type: 'string' } },
    ]);
    spec.paths['/people'] = {
      post: { operationId: 'createPerson', responses: { 200: { description: 'ok' } } },
    };
    const { dir, entry } = generateCase({
      spec,
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: {
          query: {
            mutationInvalidates: [
              { onMutations: ['createPerson'], invalidates: ['getPerson'] },
            ],
          },
        },
      },
    });
    const body = `
let matched: unknown = null;
const options = m.getCreatePersonMutationOptions({
  invalidateQueries(arg: any) {
    if (arg && typeof arg.predicate === 'function') {
      matched = arg.predicate({ queryKey: [${JSON.stringify('/people/say"hi"/abc')}] });
    }
  },
});
options.onSuccess({}, undefined, undefined);
result = matched;
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toBe(true);
  });
});
