// Security: generator-specific route helpers embed description text in literals.
import { describe, expect, it } from 'vitest';

import { ATTACK, evaluate, generateCase, simpleSpec } from '../support/harness';

const ROUTE = "/things/x',(" + ATTACK + "),'y";

describe('generated server and mock routes', () => {
  it('a route may not break out in the server framework output', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec(ROUTE),
      output: { target: './gen/gen.ts', client: 'hono' },
    });
    const out = evaluate(
      dir,
      entry,
      'result = m.default.routes.map((route: any) => route.path);',
    );
    expect(out.injected).toBe(false);
    // The route is carried as data: it is registered under exactly the described path.
    expect(out.result).toContain(ROUTE);
  });

  it('a route may not break out in generated mock handlers', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec(ROUTE),
      output: { target: './gen/gen.ts', client: 'fetch', mock: true },
    });
    const out = evaluate(dir, entry, 'result = m.getGetThingMockHandler().info.path;');
    expect(out.injected).toBe(false);
    // The route is carried as data: the handler matches exactly the described path.
    expect(out.result).toBe('*' + ROUTE);
  });
});
