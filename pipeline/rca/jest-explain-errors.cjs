// RCA only (pipeline/rca_rerun.sh), never in grading: make error-class assertions say WHAT was
// received. A hidden test that catches an error and asserts only its class
// (`expect(error).toBeInstanceOf(InputError)`) normally prints "Received constructor: TypeError"
// and nothing else; with this, the failure shows the received error's message and full stack.
/* eslint-disable */
const util = require('util');
const show = (v) =>
  v instanceof Error
    ? `${(v.constructor && v.constructor.name) || 'Error'}: ${v.message}\n${v.stack}` +
      (v.cause ? `\ncause: ${show(v.cause)}` : '')
    : util.inspect(v, { depth: 6 });
if (typeof expect !== 'undefined' && expect.extend) {
  expect.extend({
    toBeInstanceOf(received, expected) {
      const pass = received instanceof expected;
      return {
        pass,
        message: () =>
          `expect(received)${pass ? '.not' : ''}.toBeInstanceOf(${(expected && expected.name) || expected})\n\n` +
          `Received: ${show(received)}`,
      };
    },
  });
}
