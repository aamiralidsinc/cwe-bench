'use strict';

// Ordinary nested reads and writes, including every path notation the library accepts.
const test = require('node:test');
const assert = require('node:assert');
const bmoor = require('../../src/index.js');

test('functional: dot paths read and write nested values', () => {
  const target = { eins: 1, zwei: { drei: 3 } };

  assert.strictEqual(bmoor.get(target, 'eins'), 1);
  assert.strictEqual(bmoor.get(target, 'zwei.drei'), 3);
  assert.strictEqual(bmoor.get(target, ''), target);

  bmoor.set(target, 'vier.fuenf', 5);
  assert.strictEqual(target.vier.fuenf, 5);
  assert.strictEqual(bmoor.get(target, 'vier.fuenf'), 5);
});

test('functional: array and bracket path notations keep working', () => {
  const target = {};

  bmoor.set(target, ['a', 'b'], 1);
  bmoor.set(target, "['c']['d']", 2);

  assert.deepStrictEqual(target, { a: { b: 1 }, c: { d: 2 } });
  assert.strictEqual(bmoor.get(target, ['a', 'b']), 1);
  assert.strictEqual(bmoor.get(target, "['c']['d']"), 2);
});

test('functional: a setter creates missing intermediate objects', () => {
  const setter = bmoor.makeSetter('a.b.c');
  const target = {};

  setter(target, 5);

  assert.deepStrictEqual(target, { a: { b: { c: 5 } } });
  assert.strictEqual(bmoor.makeGetter('a.b.c')(target), 5);
});

test('functional: explode maps dotted keys onto nested objects', () => {
  const out = bmoor.object.explode({ 'a.b': 1, c: 2 });

  assert.deepStrictEqual(out, { a: { b: 1 }, c: 2 });
});
