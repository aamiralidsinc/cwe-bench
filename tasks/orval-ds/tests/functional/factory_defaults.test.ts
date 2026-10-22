// Functional: factory helpers still use description defaults.
import { describe, expect, it } from 'vitest';

import {
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

describe('factory helpers', () => {
  it('a date default still yields the described date', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({
          when: { type: 'string', format: 'date', default: '2020-01-01' },
        }),
      ),
      output: {
        target: './gen/gen.ts',
        client: 'fetch',
        factoryMethods: { mode: 'single' },
        override: { useDates: true },
      },
    });
    const body = `
const value = m.createThing();
result = value.when instanceof Date ? value.when.toISOString().slice(0, 10) : null;
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toBe('2020-01-01');
  });

  it('a date default with quotes yields the date its exact text denotes', () => {
    // The runtime's own reading of the description text is the expected value,
    // so the check holds whatever that reading is, as long as the text is intact.
    const first = '2020"01"01';
    const second = 'Jan 1 2020 10:00 GMT-05"30';
    const { dir, entry } = generateCase({
      spec: specWithSchema(
        objectSchema({
          first: { type: 'string', format: 'date-time', default: first },
          second: { type: 'string', format: 'date-time', default: second },
        }),
      ),
      output: {
        target: './gen/gen.ts',
        client: 'fetch',
        factoryMethods: { mode: 'single' },
        override: { useDates: true },
      },
    });
    const body = `
const value = m.createThing();
const show = (d: unknown) => (d instanceof Date ? String(d.getTime()) : 'not a Date');
result = {
  first: show(value.first) === show(new Date(${JSON.stringify(first)})),
  second: show(value.second) === show(new Date(${JSON.stringify(second)})),
};
`;
    const out = evaluate(dir, entry, body);
    expect(out.error).toBe('');
    expect(out.result).toEqual({ first: true, second: true });
  });
});
