// Functional: legitimate routes still register in server and mock output.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { evaluate, generateCase, simpleSpec } from '../support/harness';

const PARAM = [
  { name: 'thingId', in: 'path', required: true, schema: { type: 'string' } },
];

describe('server and mock routes', () => {
  it('the server output still registers a parameterised route', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/{thingId}', 'getThing', PARAM),
      output: { target: './gen/gen.ts', client: 'hono' },
    });
    const out = evaluate(
      dir,
      entry,
      'result = m.default.routes.map((route: any) => route.path);',
    );
    expect(out.error).toBe('');
    expect(out.result).toContain('/things/:thingId');
  });

  it('the mock output still builds a handler for the route', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/{thingId}', 'getThing', PARAM),
      output: { target: './gen/gen.ts', client: 'fetch', mock: true },
    });
    const source = readFileSync(join(dir, 'gen', 'gen.ts'), 'utf8');
    expect(source).toContain('*/things/:thingId');
    const out = evaluate(
      dir,
      entry,
      "result = typeof m.getGetThingMockHandler() === 'object';",
    );
    expect(out.error).toBe('');
    expect(out.result).toBe(true);
  });

  it('the server output keeps quotes and backticks in a route', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/say"hi"/`raw`/{thingId}', 'getThing', PARAM),
      output: { target: './gen/gen.ts', client: 'hono' },
    });
    const out = evaluate(
      dir,
      entry,
      'result = m.default.routes.map((route: any) => route.path);',
    );
    expect(out.error).toBe('');
    expect(out.result).toContain('/things/say"hi"/`raw`/:thingId');
  });

  it('the mock handler keeps quotes in its route', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/say"hi"/{thingId}', 'getThing', PARAM),
      output: { target: './gen/gen.ts', client: 'fetch', mock: true },
    });
    const out = evaluate(
      dir,
      entry,
      'result = m.getGetThingMockHandler().info.path;',
    );
    expect(out.error).toBe('');
    expect(out.result).toBe('*/things/say"hi"/:thingId');
  });
});
