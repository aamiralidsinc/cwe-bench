'use strict';

// The flattening helper that turns nested configuration into key paths.
const test = require('node:test');
const assert = require('node:assert');
const bmoor = require('../../src/index.js');

test('functional: implode flattens nested values and passes arrays through', () => {
  const input = {
    time: { start: 99, stop: 100 },
    id: 'woot',
    foo: { bar: { hello: 'world' } },
    arr: [{ eins: 1 }, { zwei: 2 }],
    double: [[0]],
  };

  assert.deepStrictEqual(bmoor.object.implode(input, { skipArray: true }), {
    'time.start': 99,
    'time.stop': 100,
    id: 'woot',
    'foo.bar.hello': 'world',
    arr: [{ eins: 1 }, { zwei: 2 }],
    double: [[0]],
  });
});

test('functional: implode honours a single-level ignore', () => {
  const input = {
    time: { start: 99, stop: 100 },
    id: 'woot',
    foo: { bar: { hello: 'world' } },
  };

  assert.deepStrictEqual(bmoor.object.implode(input, {
    ignore: { time: { start: true }, id: true, foo: true },
  }), {
    'time.stop': 100,
  });
});
