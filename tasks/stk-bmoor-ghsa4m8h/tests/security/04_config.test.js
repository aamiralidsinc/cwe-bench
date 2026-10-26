'use strict';

// The configuration wrapper sets, bulk-assigns and resolves sub-configuration branches.
const test = require('node:test');
const assert = require('node:assert');
const bmoor = require('../../src/index.js');

const { Config } = bmoor.lib.config;

let seq = 0;
function probe() {
  seq += 1;
  return 'bmoor_probe_' + process.pid + '_' + seq;
}
function isOnPrototype(name) {
  return Object.prototype.hasOwnProperty.call(Object.prototype, name);
}
function assertBlocked(name, label) {
  assert.strictEqual(isOnPrototype(name), false,
    label + ': the value became a property of the shared object prototype');
  assert.strictEqual(({})[name], undefined,
    label + ': every ordinary object exposes the submitted value');
}
function discard(name) {
  try { delete Object.prototype[name]; } catch (e) { /* nothing to clean */ }
}

test('security: bulk assignment refuses a payload with a prototype key', async () => {
  const name = probe();
  try {
    try {
      await new Config({}).assign(JSON.parse('{"__proto__":{"' + name + '":"attacker"}}'));
    } catch (e) { /* refusing with an error is an acceptable refusal */ }
    assertBlocked(name, 'bulk assign prototype key');
  } finally { discard(name); }
});

test('security: bulk assignment refuses a payload with a constructor chain', async () => {
  const name = probe();
  try {
    try {
      await new Config({}).assign(JSON.parse('{"constructor":{"prototype":{"' + name + '":"attacker"}}}'));
    } catch (e) { /* refusing with an error is an acceptable refusal */ }
    assertBlocked(name, 'bulk assign constructor chain');
  } finally { discard(name); }
});

test('security: a sub-configuration refuses a constructor chain path', () => {
  const name = probe();
  try {
    try {
      new Config({}).sub('constructor.prototype', JSON.parse('{"' + name + '":"attacker"}'));
    } catch (e) { /* refusing with an error is an acceptable refusal */ }
    assertBlocked(name, 'sub constructor chain path');
  } finally { discard(name); }
});
