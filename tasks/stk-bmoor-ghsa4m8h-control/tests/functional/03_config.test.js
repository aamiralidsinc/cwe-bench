'use strict';

// The configuration wrapper's defaults, bulk assignment and sub-configuration behaviour.
const test = require('node:test');
const assert = require('node:assert');
const bmoor = require('../../src/index.js');

const { Config } = bmoor.lib.config;

test('functional: configuration defaults and single-value overrides', () => {
  const config = new Config({ foo: 'eins', hello: { world: 'zwei' } });

  assert.strictEqual(config.get('foo'), 'eins');
  assert.strictEqual(config.get('hello.world'), 'zwei');

  config.set('foo', 1);
  config.set('hello.world', 2);

  assert.strictEqual(config.get('foo'), 1);
  assert.deepStrictEqual(config.get('hello'), { world: 2 });
  assert.strictEqual(config.get('hello.world'), 2);
});

test('functional: bulk assignment keeps nested values and arrays', async () => {
  const config = new Config({ arr: [0], hello: [{ world: 1 }] });

  await config.assign({ arr: [1, 2], hello: [{ world: 2 }] });

  assert.deepStrictEqual(config.get('arr'), [1, 2]);
  assert.deepStrictEqual(config.get('hello'), [{ world: 2 }]);
  assert.strictEqual(config.get('hello.0.world'), 2);
});

test('functional: sub-configurations read, merge and create branches', () => {
  const config = new Config({ a: { b: 1 } });

  assert.strictEqual(config.sub('a').get('b'), 1);

  config.sub('a', { c: 2 });
  assert.strictEqual(config.get('a.b'), 1);
  assert.strictEqual(config.get('a.c'), 2);

  const empty = new Config({});
  const branch = empty.sub('x.y', { z: 3 });
  assert.strictEqual(branch.get('z'), 3);
  assert.strictEqual(empty.get('x.y.z'), 3);
});
