'use strict';
// T6 — the library's own merge helper must treat a name that coincides with an
// inherited member as ordinary data. An ifNotSet merge still writes a key the
// destination has never set.
const {
  loadApp, assert, assertEqual, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();
const util = protobuf.util;

module.exports = [
  {
    name: 'ifNotSet merge still writes a key that only exists on the prototype',
    run() {
      const dst = {};
      util.merge(dst, { toString: 'to-string-marker' }, true);
      assert(hasOwn(dst, 'toString'), 'merge must store the key as own data');
      assertEqual(dst.toString, 'to-string-marker', 'value stored under the key');
    },
  },
  {
    name: 'ifNotSet merge still writes a key named hasOwnProperty',
    run() {
      const dst = {};
      util.merge(dst, { hasOwnProperty: 'hop-marker' }, true);
      assert(hasOwn(dst, 'hasOwnProperty'), 'merge must store the key as own data');
      assertEqual(dst.hasOwnProperty, 'hop-marker', 'value stored under the key');
    },
  },
  {
    name: 'ifNotSet merge still writes a key named valueOf',
    run() {
      const dst = {};
      util.merge(dst, { valueOf: 'value-of-marker' }, true);
      assert(hasOwn(dst, 'valueOf'), 'merge must store the key as own data');
      assertEqual(dst.valueOf, 'value-of-marker', 'value stored under the key');
    },
  },
  {
    name: 'ifNotSet merge still writes a key named isPrototypeOf',
    run() {
      const dst = {};
      util.merge(dst, { isPrototypeOf: 'ipo-marker' }, true);
      assert(hasOwn(dst, 'isPrototypeOf'), 'merge must store the key as own data');
      assertEqual(dst.isPrototypeOf, 'ipo-marker', 'value stored under the key');
    },
  },
];
