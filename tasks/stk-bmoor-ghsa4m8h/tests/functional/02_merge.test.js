'use strict';

// Deep merge semantics that other code depends on.
const test = require('node:test');
const assert = require('node:assert');
const bmoor = require('../../src/index.js');

test('functional: merge replaces nulls, keeps untouched branches and keeps arrays by reference', () => {
  const incomingArray = [4, 5];

  const out = bmoor.object.merge({
    foo: null,
    bar: { a: 'ok' },
    hello: { world: 1, other: 'thing', arr: null },
    arr: [1, 2],
    arr2: [8, 9],
  }, {
    foo: 'bar',
    bar: null,
    hello: { world: null, arr: [1, 2] },
    arr: null,
    arr2: incomingArray,
  });

  assert.deepStrictEqual(out, {
    foo: 'bar',
    bar: null,
    hello: { world: null, other: 'thing', arr: [1, 2] },
    arr: null,
    arr2: [4, 5],
  });
  assert.strictEqual(out.arr2, incomingArray);
});

test('functional: merge keeps ordinary data keys that share a built-in member name', () => {
  const out = bmoor.object.merge({}, JSON.parse('{"constructor":5,"prototype":6,"valueOf":7}'));

  assert.strictEqual(out.constructor, 5);
  assert.strictEqual(out.prototype, 6);
  assert.strictEqual(out.valueOf, 7);
});
