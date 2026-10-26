'use strict';

// Deep merge walks the enumerable keys of the source object.
const test = require('node:test');
const assert = require('node:assert');
const bmoor = require('../../src/index.js');

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
function attempt(fn) {
  try { fn(); } catch (e) { /* refusing with an error is an acceptable refusal */ }
}

test('security: merge refuses a payload with an own prototype key', () => {
  const name = probe();
  try {
    attempt(() => bmoor.object.merge({}, JSON.parse('{"__proto__":{"' + name + '":"attacker"}}')));
    assertBlocked(name, 'merge prototype key');
  } finally { discard(name); }
});

test('security: merge refuses a prototype key nested in an ordinary object', () => {
  const name = probe();
  try {
    attempt(() => bmoor.object.merge({}, JSON.parse('{"a":{"__proto__":{"' + name + '":"attacker"}}}')));
    assertBlocked(name, 'merge nested prototype key');
  } finally { discard(name); }
});

test('security: merge refuses a prototype key carrying an array value', () => {
  const name = probe();
  try {
    attempt(() => bmoor.object.merge({}, JSON.parse('{"__proto__":{"' + name + '":["attacker"]}}')));
    assertBlocked(name, 'merge prototype array value');
  } finally { discard(name); }
});
