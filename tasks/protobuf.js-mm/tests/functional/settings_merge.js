'use strict';
// Coupled behaviour: settings, merges and schema option aggregates keep working
// exactly as today.
const {
  loadApp, assert, assertEqual, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();
const util = protobuf.util;

module.exports = [
  {
    name: 'a setting that was never set still reads as absent',
    run() {
      const t = new protobuf.Type('T');
      assert(t.getOption('ordinary') === undefined, 'unset setting is absent');
    },
  },
  {
    name: 'a setting that was set is readable',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('ordinary', 42);
      assertEqual(t.getOption('ordinary'), 42, 'setting');
    },
  },
  {
    name: 'ifNotSet does not overwrite a setting that was set',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('ordinary', 'first');
      t.setOption('ordinary', 'second', true);
      assertEqual(t.getOption('ordinary'), 'first', 'ifNotSet keeps the first value');
    },
  },
  {
    name: 'util.merge copies ordinary keys',
    run() {
      const dst = { a: 1 };
      util.merge(dst, { b: 2, c: 3 });
      assertEqual(dst.b, 2, 'b');
      assertEqual(dst.c, 3, 'c');
      assertEqual(dst.a, 1, 'a untouched');
    },
  },
  {
    name: 'util.merge ifNotSet does not overwrite an own key',
    run() {
      const dst = { toString: 'first' };
      util.merge(dst, { toString: 'second' }, true);
      assertEqual(dst.toString, 'first', 'ifNotSet keeps the first value');
    },
  },
  {
    name: 'util.merge without ifNotSet writes a shadowing key as ordinary data',
    run() {
      const dst = {};
      util.merge(dst, { toString: 'to-string-marker', ordinary: 1 });
      assert(hasOwn(dst, 'toString'), 'merge must store the key as own data');
      assertEqual(dst.toString, 'to-string-marker', 'value stored under the key');
      assertEqual(dst.ordinary, 1, 'ordinary key unchanged');
    },
  },
  {
    name: 'an ordinary option aggregate member is stored as the literal',
    run() {
      const root = protobuf.parse(
        'syntax="proto2"; message M { option (my.opt) = { ordinary: "marker" other: 7 }; optional string f = 1; }',
        { keepCase: false },
      ).root;
      const bag = root.lookupType('M').parsedOptions[0]['(my.opt)'];
      assertEqual(bag.ordinary, 'marker', 'string member');
      assertEqual(bag.other, 7, 'number member');
    },
  },
  {
    name: 'an option aggregate repeats a member into a list',
    run() {
      const root = protobuf.parse(
        'syntax="proto2"; message M { option (my.opt) = { items: "a" items: "b" }; optional string f = 1; }',
        { keepCase: false },
      ).root;
      const bag = root.lookupType('M').parsedOptions[0]['(my.opt)'];
      assertEqual(bag.items.length, 2, 'repeated member');
    },
  },
  {
    name: 'an ifNotSet write does not overwrite a setting that was set',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('toString', 'first');
      t.setOption('toString', 'second', true);
      assertEqual(t.getOption('toString'), 'first', 'ifNotSet keeps the first value');
    },
  },
];
