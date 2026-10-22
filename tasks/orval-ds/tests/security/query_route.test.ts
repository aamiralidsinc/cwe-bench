// Security: the same route text is also emitted into query-side cache keys.
import { describe, expect, it } from 'vitest';

import { ATTACK, evaluate, generateCase, simpleSpec } from '../support/harness';

const SEGMENT = "x',(" + ATTACK + "),'y";
const PARAM = [
  { name: 'thingId', in: 'path', required: true, schema: { type: 'string' } },
];

describe('generated query keys', () => {
  it('a static segment may not break out of an array query key', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/' + SEGMENT + '/{thingId}', 'getThing', PARAM),
      output: {
        target: './gen/gen.ts',
        client: 'react-query',
        override: { query: { shouldSplitQueryKey: true } },
      },
    });
    const out = evaluate(dir, entry, "result = m.getGetThingQueryKey('id');");
    expect(out.injected).toBe(false);
    // The segment is carried as data: the key still holds exactly the described text.
    expect(out.result).toEqual(['things', SEGMENT, 'id']);
  });

  it('an invalidation prefix may not break out of a quoted prefix', () => {
    const spec = simpleSpec('/people/' + SEGMENT + '/{personId}', 'getPerson', [
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
const options = m.getCreatePersonMutationOptions({
  invalidateQueries(arg: any) {
    if (arg && typeof arg.predicate === 'function') {
      arg.predicate({ queryKey: ['/people/x', 1, '/y'] });
    }
  },
});
options.onSuccess({}, undefined, undefined);
`;
    expect(evaluate(dir, entry, body).injected).toBe(false);
    // The prefix is carried as data: it still matches the exact described route.
    const matchBody = `
let matched: unknown = null;
const options = m.getCreatePersonMutationOptions({
  invalidateQueries(arg: any) {
    if (arg && typeof arg.predicate === 'function') {
      matched = arg.predicate({ queryKey: [${JSON.stringify('/people/' + SEGMENT + '/abc')}] });
    }
  },
});
options.onSuccess({}, undefined, undefined);
result = matched;
`;
    const out = evaluate(dir, entry, matchBody);
    expect(out.injected).toBe(false);
    expect(out.result).toBe(true);
  });
});
