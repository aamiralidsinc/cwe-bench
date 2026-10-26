'use strict';

// The setter factory builds closures that assign into their context directly.
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

test('security: a setter for a prototype-hook path is refused', () => {
  const name = probe();
  try {
    attempt(() => bmoor.makeSetter('__proto__.' + name)({}, 'attacker'));
    assertBlocked(name, 'setter __proto__ path');
  } finally { discard(name); }
});

test('security: a setter for a constructor chain is refused', () => {
  const name = probe();
  try {
    attempt(() => bmoor.makeSetter('constructor.prototype.' + name)({}, 'attacker'));
    assertBlocked(name, 'setter constructor chain');
  } finally { discard(name); }
});

test('security: a setter built from an array path with a prototype element is refused', () => {
  const name = probe();
  try {
    attempt(() => bmoor.makeSetter([['__proto__'], name])({}, 'attacker'));
    assertBlocked(name, 'setter array path');
  } finally { discard(name); }
});

test('security: an exploder built from a prototype-hook path is refused', () => {
  const name = probe();
  try {
    attempt(() => bmoor.object.makeExploder(['__proto__.' + name])({}));
    assertBlocked(name, 'exploder path');
  } finally { discard(name); }
});
