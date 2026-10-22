'use strict';
// T3 — an enum identifier taken from the wire must resolve against the enum's
// own values. A name the enum never declared is invalid; it is never resolved to
// a value the values table happens to inherit. A name the enum did declare is
// ordinary data: it must be addable, storable and readable like any other name.
const {
  loadApp, assert, assertEqual, snapshotBuiltins, assertBuiltinsClean,
  parseRoot, assertClientError, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();

const SCHEMA = `
syntax = "proto3";
enum Kind { OK = 0; OTHER = 1; }
message M { Kind kind = 1; }
`;

const DECLARED = `
syntax = "proto3";
enum Kind { constructor = 0; toString = 1; OK = 2; }
message M { Kind kind = 1; }
`;

function msgType(src, name) {
  const root = parseRoot(protobuf, src);
  return root.lookupType(name);
}

module.exports = [
  {
    name: 'an undeclared enum identifier constructor is rejected',
    run() {
      const type = msgType(SCHEMA, 'M');
      assertClientError(() => type.fromText('kind: constructor'), 'enum identifier constructor');
      const msg = type.fromText('kind: OK');
      assertEqual(msg.kind, 0, 'ordinary identifier still parses');
    },
  },
  {
    name: 'an undeclared enum identifier toString is rejected',
    run() {
      const type = msgType(SCHEMA, 'M');
      assertClientError(() => type.fromText('kind: toString'), 'enum identifier toString');
      const msg = type.fromText('kind: OTHER');
      assertEqual(msg.kind, 1, 'ordinary identifier still parses');
    },
  },
  {
    name: 'an undeclared enum identifier hasOwnProperty is rejected',
    run() {
      const type = msgType(SCHEMA, 'M');
      assertClientError(() => type.fromText('kind: hasOwnProperty'), 'enum identifier hasOwnProperty');
    },
  },
  {
    name: 'an undeclared enum identifier valueOf is rejected',
    run() {
      const type = msgType(SCHEMA, 'M');
      assertClientError(() => type.fromText('kind: valueOf'), 'enum identifier valueOf');
    },
  },
  {
    name: 'a values table never reports an inherited member as a value',
    run() {
      const root = parseRoot(protobuf, SCHEMA);
      const enm = root.lookupEnum('Kind');
      const before = snapshotBuiltins();
      for (const name of ['constructor', 'toString', 'hasOwnProperty', 'valueOf', 'isPrototypeOf']) {
        assert(
          enm.values[name] === undefined,
          'undeclared name ' + name + ' must not resolve to a value, got ' + String(enm.values[name]),
        );
      }
      assertBuiltinsClean(before, 'values-table lookup');
    },
  },
  {
    name: 'an enum value named constructor can be added',
    run() {
      const enm = new protobuf.Enum('E', { OK: 0 });
      enm.add('constructor', 1);
      assertEqual(enm.values.constructor, 1, 'added value');
      assertEqual(enm.valuesById[1], 'constructor', 'reverse lookup');
    },
  },
  {
    name: 'an enum value named toString can be added',
    run() {
      const enm = new protobuf.Enum('E', { OK: 0 });
      enm.add('toString', 1);
      assertEqual(enm.values.toString, 1, 'added value');
      assertEqual(enm.valuesById[1], 'toString', 'reverse lookup');
    },
  },
  {
    name: 'a schema may declare an enum value named constructor',
    run() {
      const type = msgType(DECLARED, 'M');
      const msg = type.fromText('kind: constructor');
      assertEqual(msg.kind, 0, 'declared value resolves to its number');
    },
  },
  {
    name: 'a schema may declare an enum value named toString',
    run() {
      const type = msgType(DECLARED, 'M');
      const msg = type.fromText('kind: toString');
      assertEqual(msg.kind, 1, 'declared value resolves to its number');
    },
  },
];
