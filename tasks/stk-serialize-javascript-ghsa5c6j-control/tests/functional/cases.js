'use strict';

/*
 * Functional cases: the documented behaviour of the library and the legitimate values that sit
 * next to the hidden ones. Every expectation below is what the pinned library already produces
 * today; these must keep working whatever the fix does. Expected strings are literals.
 */

const DATE = new Date('2016-04-28T22:02:17.156Z');
const DATE_OUT = 'new Date("2016-04-28T22:02:17.156Z")';

module.exports = function (serialize) {
  const cases = [];
  const add = (id, name, makeInput, expected, options) => cases.push({
    classname: 'functional/' + id,
    name: `${id}: ${name}`,
    run() {
      const input = makeInput();
      const got = options === undefined ? serialize(input) : serialize(input, options);
      if (got !== expected) {
        throw new Error(`serialize() returned ${JSON.stringify(got)}, expected ${JSON.stringify(expected)}`);
      }
    },
  });

  // Regular expressions: the documented output, including through a subclass that reports its
  // own flags the ordinary way.
  add('F-regexp-plain', 'a literal regular expression keeps its exact output',
      () => /asdf/, 'new RegExp("asdf", "")');
  add('F-regexp-flags', 'a regular expression with flags keeps them exactly',
      () => /^asdf$/gi, 'new RegExp("^asdf$", "gi")');
  add('F-regexp-subclass', 'a regular-expression subclass reporting ordinary flags keeps its output',
      () => { class Sub extends RegExp { get flags() { return super.flags; } } return new Sub('^asdf$', 'gi'); },
      'new RegExp("^asdf$", "gi")');
  add('F-regexp-nested', 'a regular expression nested in an object keeps its output',
      () => ({ t: [/a/g] }), '{"t":[new RegExp("a", "g")]}');
  add('F-regexp-escaped', 'a regular expression with escaped characters keeps its output',
      () => /\..*/, 'new RegExp("\\\\..*", "")');

  // Dates: the documented output, including through a subclass that computes its ISO text.
  add('F-date', 'a date keeps its exact output', () => DATE, DATE_OUT);
  add('F-date-nested', 'a date nested in an object keeps its exact output',
      () => ({ t: [DATE] }), `{"t":[${DATE_OUT}]}`);
  add('F-date-subclass', 'a date subclass computing the ordinary ISO text keeps its output',
      () => { class Sub extends Date { toISOString() { return super.toISOString(); } } return new Sub(DATE.getTime()); },
      DATE_OUT);
  add('F-iso-string', 'a string that looks like an ISO date stays a string',
      () => '2016-04-28T22:02:17.156Z', '"2016-04-28T22:02:17.156Z"');
  add('F-iso-string-nested', 'a string that looks like an ISO date stays a string when nested',
      () => ({ when: '2016-04-28T22:02:17.156Z' }), '{"when":"2016-04-28T22:02:17.156Z"}');

  // Ordinary computed and container values keep working.
  add('F-stable-getter', 'a property whose accessor returns a stable value keeps that value',
      () => { const o = {}; Object.defineProperty(o, 'x', { enumerable: true, get() { return 'stable'; } }); return o; },
      '{"x":"stable"}');
  add('F-tojson-object', 'an object declaring a string JSON form keeps that form',
      () => ({ a: { toJSON: function () { return 'declared'; } } }), '{"a":"declared"}');
  add('F-proxy-plain', 'an ordinary proxy around a plain object serializes like the object',
      () => new Proxy({ a: 1, d: DATE }, {}), `{"a":1,"d":${DATE_OUT}}`);

  // The option that drops functions keeps dropping them, on ordinary values.
  add('F-ignore-function', 'functions are still omitted when asked',
      () => ({ num: 1, fn: function () { return true; } }), '{"num":1}', { ignoreFunction: true });
  add('F-ignore-function-nested', 'nested functions are still omitted when asked',
      () => ({ o: { num: 1, fn: function () { return true; } } }), '{"o":{"num":1}}', { ignoreFunction: true });
  add('F-ignore-function-proxy', 'functions in an ordinary proxy are still omitted when asked',
      () => new Proxy({ num: 1, fn: function () { return true; } }, {}), '{"num":1}', { ignoreFunction: true });

  // The other documented behaviours around the fix.
  add('F-unsafe', 'the unsafe option still leaves HTML characters alone',
      () => ['<'], '["<"]', { unsafe: true });
  add('F-escaped-default', 'HTML characters are still escaped by default',
      () => ['<'], '["\\u003C"]');
  add('F-function', 'a function is still serialized as its own source',
      () => { function f() { return 1; } return f; }, 'function f() { return 1; }');
  add('F-map', 'a map keeps its exact output', () => new Map([['a', 123]]), 'new Map([["a",123]])');
  add('F-set', 'a set with a regular expression keeps its exact output',
      () => new Set(['a', /x/]), 'new Set(["a",new RegExp("x", "")])');
  add('F-undefined', 'an undefined property is still serialized as undefined',
      () => ({ u: undefined }), '{"u":undefined}');
  add('F-infinity', 'Infinity is still serialized as Infinity',
      () => ({ i: Infinity }), '{"i":Infinity}');

  return cases;
};
