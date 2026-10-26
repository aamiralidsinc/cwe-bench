'use strict';
/* Shared helpers for the hidden cases. Expected values are literals in the case tables. */
const vm = require('vm');

function sandbox() {
  const box = { Date, RegExp, Map, Set, Array, Object, String, Number, Boolean, JSON, Math, Error };
  box.__hidden_marker__ = 0;
  box.globalThis = box;
  return box;
}

// Serialize input (any refusal is a valid answer), then evaluate the result in an isolated
// context. Reports whether the supplied payload managed to run.
function run(serialize, input, options) {
  let out;
  try {
    out = arguments.length > 2 ? serialize(input, options) : serialize(input);
  } catch (e) {
    return { refused: true, error: e, out: null, pwned: false, value: undefined, evalError: null };
  }
  const box = sandbox();
  let value, evalError = null;
  try { value = vm.runInNewContext('(' + out + '\n)', box, { timeout: 2000 }); }
  catch (e) { evalError = e; }
  return { refused: false, out, evalError, value, pwned: box.__hidden_marker__ === 1 };
}

module.exports = { run, sandbox };
