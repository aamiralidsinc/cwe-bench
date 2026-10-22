// Security: description route and base-URL text is emitted into client modules.
import { describe, expect, it } from 'vitest';

import { ATTACK, evaluate, generateCase, simpleSpec } from '../support/harness';

const BACKTICK = '`+(' + ATTACK + ')+`';

describe('generated request URLs', () => {
  it('static path text may not break out of the URL template literal', () => {
    const { dir, entry } = generateCase({
      spec: simpleSpec('/things/x' + BACKTICK + '/y'),
      output: { target: './gen/gen.ts', client: 'fetch' },
    });
    const out = evaluate(dir, entry, 'result = m.getGetThingUrl();');
    expect(out.injected).toBe(false);
    // The text is carried as data: the URL holds exactly the described text.
    expect(out.result).toBe('/things/x' + BACKTICK + '/y');
  });

  it('a server URL from the description may not break out', () => {
    const spec = simpleSpec('/things');
    spec.servers = [{ url: 'http://api.example/' + BACKTICK }];
    const { dir, entry } = generateCase({
      spec,
      output: {
        target: './gen/gen.ts',
        client: 'fetch',
        baseUrl: { getBaseUrlFromSpecification: true },
      },
    });
    const out = evaluate(dir, entry, 'result = m.getGetThingUrl();');
    expect(out.injected).toBe(false);
    // The text is carried as data: the URL holds exactly the described text.
    expect(out.result).toBe('http://api.example/' + BACKTICK + '/things');
  });

  it('a server variable default may not break out', () => {
    const spec = simpleSpec('/things');
    spec.servers = [
      {
        url: 'http://{env}.example',
        variables: { env: { default: BACKTICK } },
      },
    ];
    const { dir, entry } = generateCase({
      spec,
      output: {
        target: './gen/gen.ts',
        client: 'fetch',
        baseUrl: { getBaseUrlFromSpecification: true },
      },
    });
    const out = evaluate(dir, entry, 'result = m.getGetThingUrl();');
    expect(out.injected).toBe(false);
    // The text is carried as data: the URL holds exactly the described text.
    expect(out.result).toBe('http://' + BACKTICK + '.example/things');
  });
});
