'use strict';
const { run } = require('../support/harness.js');

// The payload runs only if the library writes the supplied text into the output as code.
const MARK = 'x"+(globalThis.__hidden_marker__=1)+"';

function notRun(r, what) {
  if (r.refused) return;
  if (r.pwned) throw new Error(what + ' ran as code: ' + r.out);
}
function represented(r, expected, what) {
  if (r.refused) return;
  if (r.evalError) throw new Error('the output could not be used: ' + r.evalError.message + ' :: ' + r.out);
  if (!r.value || r.value.field !== expected) throw new Error(what + ': ' + r.out);
}

module.exports = function (serialize) {
  const cases = [];
  const add = (classname, name, run_) => cases.push({ classname, name, run: run_ });

  // T1: regular-expression flag text is written into the output as source.
  add('security/T1', 'flag text supplied through an own property', function () {
    const re = /abc/g;
    Object.defineProperty(re, 'flags', { value: MARK, configurable: true });
    notRun(run(serialize, { re }), 'the supplied flag text');
  });
  add('security/T1', 'flag text supplied through a computed accessor', function () {
    class Spoofed extends RegExp { get flags() { return MARK; } }
    notRun(run(serialize, { re: new Spoofed('a') }), 'the supplied flag text');
  });
  add('security/T1', 'flag text of a deeply nested expression', function () {
    class Spoofed extends RegExp { get flags() { return MARK; } }
    notRun(run(serialize, { a: { b: [new Spoofed('z')] } }), 'the supplied flag text');
  });
  add('security/T1', 'flag text in a top-level array', function () {
    class Spoofed extends RegExp { get flags() { return MARK; } }
    notRun(run(serialize, [new Spoofed('q')]), 'the supplied flag text');
  });

  // T2: date text is written into the output as source.
  add('security/T2', 'date text supplied through a computed accessor', function () {
    class SpoofedDate extends Date { toISOString() { return MARK; } }
    notRun(run(serialize, { d: new SpoofedDate('2020-01-01T00:00:00.000Z') }), 'the supplied date text');
  });
  add('security/T2', 'date text in a top-level array', function () {
    class SpoofedDate extends Date { toISOString() { return MARK; } }
    notRun(run(serialize, [new SpoofedDate('2020-01-01T00:00:00.000Z')]), 'the supplied date text');
  });
  add('security/T2', 'date text nested in a map value', function () {
    class SpoofedDate extends Date { toISOString() { return MARK; } }
    notRun(run(serialize, { m: new Map([['when', new SpoofedDate('2020-01-01T00:00:00.000Z')]]) }), 'the supplied date text');
  });

  // T6: dispatch must use the value that was serialized.
  add('security/T6', 'a second read that yields a function', function () {
    let reads = 0;
    const holder = {};
    Object.defineProperty(holder, 'field', { enumerable: true, configurable: true,
      get() { reads += 1; return reads === 1 ? 'plain description' : function leak() { globalThis.__hidden_marker__ = 1; }; } });
    represented(run(serialize, holder), 'plain description', 'the output does not rebuild the serialized string');
  });
  add('security/T6', 'a second read that yields a regular expression', function () {
    let reads = 0;
    const holder = {};
    Object.defineProperty(holder, 'field', { enumerable: true, configurable: true,
      get() { reads += 1; return reads === 1 ? 'plain description' : /needle/; } });
    represented(run(serialize, holder), 'plain description', 'the output does not rebuild the serialized string');
  });
  add('security/T6', 'a function that declares a string JSON form', function () {
    function handler() { globalThis.__hidden_marker__ = 1; }
    handler.toJSON = function () { return 'plain description'; };
    represented(run(serialize, { field: handler }), 'plain description', 'the output does not rebuild the declared JSON value');
  });

  // T7: the caller asked for functions to be omitted.
  add('security/T7', 'an object whose delete does not remove a function', function () {
    const target = { label: 'kept', handler() { globalThis.__hidden_marker__ = 1; } };
    const proxy = new Proxy(target, { deleteProperty() { return true; } });
    const r = run(serialize, proxy, { ignoreFunction: true });
    if (r.refused) return;
    if (r.evalError) throw new Error('the output could not be used: ' + r.evalError.message + ' :: ' + r.out);
    if (!r.value || r.value.label !== 'kept') throw new Error('the kept value is missing: ' + r.out);
    if (typeof r.value.handler !== 'undefined') throw new Error('a function that was asked to be omitted is in the output: ' + r.out);
  });
  add('security/T7', 'a nested object whose delete does not remove a function', function () {
    const inner = new Proxy({ keep: 1, handler() { globalThis.__hidden_marker__ = 1; } }, { deleteProperty() { return true; } });
    const r = run(serialize, { outer: inner }, { ignoreFunction: true });
    if (r.refused) return;
    if (r.evalError) throw new Error('the output could not be used: ' + r.evalError.message + ' :: ' + r.out);
    if (!r.value || !r.value.outer || r.value.outer.keep !== 1) throw new Error('the kept value is missing: ' + r.out);
    if (typeof r.value.outer.handler !== 'undefined') throw new Error('a nested function that was asked to be omitted is in the output: ' + r.out);
  });
  return cases;
};
