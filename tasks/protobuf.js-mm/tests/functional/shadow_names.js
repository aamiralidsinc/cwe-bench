'use strict';
// Coupled behaviour: names that already work today must keep working after a
// fix. An over-broad guard that refuses a name because it looks inherited, or
// that drops the entry, fails here.
const {
  loadApp, assert, assertEqual, assertOwnData, parseType, parseRoot, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();

const SCHEMA = `
syntax = "proto3";
message Shade {
  string constructor = 1;
  string to_string = 2;
  map<string, string> plain = 3;
}
`;

module.exports = [
  {
    name: 'a singular field named constructor still parses',
    run() {
      const msg = parseType(protobuf, SCHEMA, 'Shade').fromText('constructor: "marker"');
      assertEqual(msg.constructor, 'marker', 'value');
    },
  },
  {
    name: 'a singular field named to_string still parses',
    run() {
      const msg = parseType(protobuf, SCHEMA, 'Shade').fromText('to_string: "marker"');
      assertEqual(msg.toString, 'marker', 'value');
    },
  },
  {
    name: 'a setting named toString can be written and read',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('toString', 'marker');
      assertEqual(t.getOption('toString'), 'marker', 'setting');
    },
  },
  {
    name: 'a setting named constructor can be written and read',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('constructor', 'marker');
      assertEqual(t.getOption('constructor'), 'marker', 'setting');
    },
  },
  {
    name: 'a setting named toString can be written and read after another setting',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('ordinary', 'seed');
      t.setOption('toString', 'marker');
      assertEqual(t.getOption('toString'), 'marker', 'setting');
    },
  },
  {
    name: 'an ordinary setting still reads as absent when never set',
    run() {
      const t = new protobuf.Type('T');
      t.setOption('ordinary', 'seed');
      assert(t.getOption('other') === undefined, 'unset setting is absent');
    },
  },
  {
    name: 'Enum#add of the reserved name __proto__ is still ignored',
    run() {
      const enm = new protobuf.Enum('E', { OK: 0 });
      enm.add('__proto__', 9);
      assert(!hasOwn(enm.values, '__proto__'), 'reserved name is not added');
      assertEqual(enm.values.OK, 0, 'ordinary value untouched');
    },
  },
  {
    name: 'a generated enum table keeps ordinary names as own data',
    run() {
      const { pbjsStatic } = require('../support/lib');
      const root = pbjsStatic(protobuf, 'syntax="proto3"; enum Kind { first = 0; second = 1; OK = 2; }');
      assert(hasOwn(root.Kind, 'first'), 'first is own data');
      assert(hasOwn(root.Kind, 'second'), 'second is own data');
      assertEqual(root.Kind[2], 'OK', 'id -> name');
    },
  },
  {
    name: 'a map of ordinary keys keeps working beside shadowing field names',
    run() {
      const msg = parseType(protobuf, SCHEMA, 'Shade').fromText('plain { key: "a" value: "1" } constructor: "c"');
      assertEqual(msg.plain.a, '1', 'map entry');
      assertEqual(msg.constructor, 'c', 'shadowing field');
    },
  },
];
