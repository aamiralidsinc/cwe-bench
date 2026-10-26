'use strict';

// The library's deep-set entry point, exercised with every path shape it accepts.
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

test('security: set refuses a dot path through the prototype hook', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, '__proto__.' + name, 'attacker'));
    assertBlocked(name, 'set __proto__ path');
  } finally { discard(name); }
});

test('security: set refuses a dot path through a constructor chain', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, 'constructor.prototype.' + name, 'attacker'));
    assertBlocked(name, 'set constructor chain');
  } finally { discard(name); }
});

test('security: set refuses a prototype segment below an ordinary key', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, 'safe.__proto__.' + name, 'attacker'));
    assertBlocked(name, 'set nested prototype segment');
  } finally { discard(name); }
});

test('security: set refuses a flat array path naming the prototype hook', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, ['__proto__', name], 'attacker'));
    assertBlocked(name, 'set array path');
  } finally { discard(name); }
});

test('security: set refuses an array path whose element names the prototype hook', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, [['__proto__'], name], 'attacker'));
    assertBlocked(name, 'set nested-element array path');
  } finally { discard(name); }
});

test('security: set refuses a bracket and quoted path naming the prototype hook', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, "['__proto__']['" + name + "']", 'attacker'));
    assertBlocked(name, 'set bracket path');
  } finally { discard(name); }
});

test('security: set refuses a bracket path through a constructor chain', () => {
  const name = probe();
  try {
    attempt(() => bmoor.set({}, "['constructor']['prototype']['" + name + "']", 'attacker'));
    assertBlocked(name, 'set bracket constructor chain');
  } finally { discard(name); }
});

test('security: explode refuses a dotted key through a constructor chain', () => {
  const name = probe();
  try {
    attempt(() => bmoor.object.explode({ ['constructor.prototype.' + name]: 'attacker' }));
    assertBlocked(name, 'explode dotted key');
  } finally { discard(name); }
});
