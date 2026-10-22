'use strict';
// T4 — a setting that was never set reads as absent. Reading must not return an
// inherited member; writing must store under the name given, even when that
// name coincides with a member every object inherits.
const {
  loadApp, assert, assertEqual, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();

function typeWithSettings() {
  const t = new protobuf.Type('T');
  // Materialise the settings container so a subsequent read can see inherited
  // members of the plain object the library stores settings on.
  t.setOption('ordinary', 'seed');
  return t;
}

module.exports = [
  {
    name: 'reading an unset setting named toString reports absent',
    run() {
      const t = typeWithSettings();
      const v = t.getOption('toString');
      assert(v === undefined, 'unset setting must read as absent, got ' + String(v));
    },
  },
  {
    name: 'reading an unset setting named constructor reports absent',
    run() {
      const t = typeWithSettings();
      const v = t.getOption('constructor');
      assert(v === undefined, 'unset setting must read as absent, got ' + String(v));
    },
  },
  {
    name: 'reading an unset setting named hasOwnProperty reports absent',
    run() {
      const t = typeWithSettings();
      const v = t.getOption('hasOwnProperty');
      assert(v === undefined, 'unset setting must read as absent, got ' + String(v));
    },
  },
  {
    name: 'reading an unset setting named valueOf reports absent',
    run() {
      const t = typeWithSettings();
      const v = t.getOption('valueOf');
      assert(v === undefined, 'unset setting must read as absent, got ' + String(v));
    },
  },
  {
    name: 'an ifNotSet write of a shadowing name still stores the value',
    run() {
      const t = typeWithSettings();
      t.setOption('toString', 'marker', true);
      assertEqual(t.getOption('toString'), 'marker', 'ifNotSet must treat an unset setting as unset');
      assert(t.options && hasOwn(t.options, 'toString'), 'setting must be stored as own data');
    },
  },
  {
    name: 'an ifNotSet write of a shadowing name named constructor still stores the value',
    run() {
      const t = typeWithSettings();
      t.setOption('constructor', 'marker', true);
      assertEqual(t.getOption('constructor'), 'marker', 'ifNotSet must treat an unset setting as unset');
      assert(t.options && hasOwn(t.options, 'constructor'), 'setting must be stored as own data');
    },
  },
];
