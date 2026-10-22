'use strict';
// T2 — a declared field whose name coincides with a member every object
// inherits is still an ordinary field. Parsing must not crash on the inherited
// member and must not write through it onto a shared built-in.
const {
  loadApp, assert, assertEqual, assertOwnData, assertOrdinaryShape,
  snapshotBuiltins, assertBuiltinsClean, parseType, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();

const SCHEMA = `
syntax = "proto3";
message Child { bool admin = 1; string role = 2; }
message Shade {
  repeated string to_string = 1;
  map<string, string> has_own_property = 2;
  repeated int32 value_of = 3;
  repeated Child is_prototype_of = 4;
  map<string, Child> property_is_enumerable = 5;
}
`;

function shade() {
  return parseType(protobuf, SCHEMA, 'Shade');
}

module.exports = [
  {
    name: 'a repeated field named to_string parses into a real array',
    run() {
      const before = snapshotBuiltins();
      const msg = shade().fromText('to_string: ["a", "b"]');
      assertBuiltinsClean(before, 'repeated to_string');
      assert(hasOwn(msg, 'toString'), 'field must be stored as an own property');
      assert(Array.isArray(msg.toString), 'repeated field must be an array, got ' + typeof msg.toString);
      assertEqual(msg.toString.length, 2, 'array length');
      assertEqual(msg.toString[0], 'a', 'array[0]');
      assertEqual(msg.toString[1], 'b', 'array[1]');
    },
  },
  {
    name: 'a map field named has_own_property parses into a real map',
    run() {
      const before = snapshotBuiltins();
      const msg = shade().fromText('has_own_property { key: "k" value: "v" }');
      assertBuiltinsClean(before, 'map has_own_property');
      assert(hasOwn(msg, 'hasOwnProperty'), 'field must be stored as an own property');
      const map = msg.hasOwnProperty;
      assert(map != null && typeof map === 'object' && typeof map !== 'function',
        'map field must be a plain object, got ' + typeof map);
      assertOwnData(map, 'k', 'v', 'has_own_property map');
      assertOrdinaryShape(map, 'has_own_property map');
    },
  },
  {
    name: 'a repeated field named value_of parses into a real array',
    run() {
      const before = snapshotBuiltins();
      const msg = shade().fromText('value_of: [1, 2, 3]');
      assertBuiltinsClean(before, 'repeated value_of');
      assert(hasOwn(msg, 'valueOf'), 'field must be stored as an own property');
      assert(Array.isArray(msg.valueOf), 'repeated field must be an array');
      assertEqual(msg.valueOf.length, 3, 'array length');
      assertEqual(msg.valueOf[2], 3, 'array[2]');
    },
  },
  {
    name: 'a repeated message field named is_prototype_of parses into a real list',
    run() {
      const before = snapshotBuiltins();
      const msg = shade().fromText('is_prototype_of { admin: true role: "owner" }');
      assertBuiltinsClean(before, 'repeated message is_prototype_of');
      assert(hasOwn(msg, 'isPrototypeOf'), 'field must be stored as an own property');
      assert(Array.isArray(msg.isPrototypeOf), 'repeated field must be an array, got ' + typeof msg.isPrototypeOf);
      assertEqual(msg.isPrototypeOf.length, 1, 'list length');
      assertEqual(msg.isPrototypeOf[0].admin, true, 'child field admin');
      assertEqual(msg.isPrototypeOf[0].role, 'owner', 'child field role');
    },
  },
  {
    name: 'a map field named property_is_enumerable parses into a real map',
    run() {
      const before = snapshotBuiltins();
      const msg = shade().fromText('property_is_enumerable { key: "k" value { admin: true } }');
      assertBuiltinsClean(before, 'map property_is_enumerable');
      assert(hasOwn(msg, 'propertyIsEnumerable'), 'field must be stored as an own property');
      const map = msg.propertyIsEnumerable;
      assert(map != null && typeof map === 'object' && typeof map !== 'function',
        'map field must be a plain object');
      assert(map.k && map.k.admin === true, 'map entry readable');
    },
  },
];
