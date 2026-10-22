// Functional: quoted property names stay single data keys in mock objects.
import { describe, expect, it } from 'vitest';

import {
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

describe('generated mock objects', () => {
  it('a quoted property name stays one key', () => {
    // Not an identifier, so the generated mock has to quote it as a key.
    const name = 'my-note "draft" `v2` ${id}';
    const { dir } = generateCase({
      spec: specWithSchema(
        objectSchema({ [name]: { type: 'string' }, note: { type: 'string' } }),
      ),
      output: {
        target: './api/gen.ts',
        client: 'fetch',
        mode: 'split',
        mock: true,
      },
    });
    const body = `
const mock = m.getGetThingResponseMock();
result = Object.keys(mock);
`;
    const out = evaluate(dir, './api/gen.faker.ts', body);
    expect(out.error).toBe('');
    expect(out.result).toEqual([name, 'note']);
  });
});
