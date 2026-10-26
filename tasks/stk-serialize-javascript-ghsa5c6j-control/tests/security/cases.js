'use strict';
const { run } = require('../support/harness.js');

// The payload runs only if the library writes the supplied text into the output as code.
const MARK = 'x"+(globalThis.__hidden_marker__=1)+"';

function notRun(r, what) {
  if (r.refused) return;
  if (r.pwned) throw new Error(what + ' ran as code: ' + r.out);
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
  return cases;
};
