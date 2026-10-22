'use strict';
// Coupled behaviour: ordinary messages, maps, enums and settings keep working
// exactly as today. A fix that is too broad fails here.
const {
  loadApp, assert, assertEqual, assertOwnData, assertOrdinaryShape, parseType, parseRoot, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();

const SCHEMA = `
syntax = "proto3";
message Note { bool admin = 1; string role = 2; }
message Envelope {
  map<string, Note> labels = 1;
  map<string, string> tags = 2;
  repeated string items = 3;
  string title = 4;
}
enum Kind { OK = 0; OTHER = 1; }
message WithEnum { Kind kind = 1; }
`;

module.exports = [
  {
    name: 'ordinary maps parse with any number of entries',
    run() {
      const type = parseType(protobuf, SCHEMA, 'Envelope');
      const msg = type.fromText(
        'labels { key: "a" value { admin: false } } ' +
        'labels { key: "b" value { admin: true role: "owner" } } ' +
        'tags { key: "x" value: "1" } tags { key: "y" value: "2" } ' +
        'items: ["one", "two"] title: "hello"',
      );
      assertEqual(Object.keys(msg.labels).length, 2, 'two label entries');
      assertOwnData(msg.labels, 'a', undefined, 'labels');
      assertOwnData(msg.labels, 'b', undefined, 'labels');
      assertEqual(msg.labels.a.admin, false, 'entry a');
      assertEqual(msg.labels.b.role, 'owner', 'entry b');
      assertEqual(msg.tags.x, '1', 'tag x');
      assertEqual(msg.tags.y, '2', 'tag y');
      assertEqual(msg.items.length, 2, 'items');
      assertEqual(msg.title, 'hello', 'title');
    },
  },
  {
    name: 'ordinary maps parse in the angle form',
    run() {
      const type = parseType(protobuf, SCHEMA, 'Envelope');
      const msg = type.fromText('labels < key: "a" value < admin: true > >');
      assertEqual(msg.labels.a.admin, true, 'angle-form entry');
    },
  },
  {
    name: 'ordinary repeated and singular fields keep working',
    run() {
      const type = parseType(protobuf, SCHEMA, 'Envelope');
      const msg = type.fromText('items: ["a"] title: "t"');
      assertEqual(msg.items[0], 'a', 'item');
      assertEqual(msg.title, 't', 'title');
    },
  },
  {
    name: 'ordinary enum identifiers parse to their numbers',
    run() {
      const type = parseType(protobuf, SCHEMA, 'WithEnum');
      assertEqual(type.fromText('kind: OK').kind, 0, 'OK');
      assertEqual(type.fromText('kind: OTHER').kind, 1, 'OTHER');
    },
  },
  {
    name: 'an enum values table keeps its numeric-to-name lookup',
    run() {
      const root = parseRoot(protobuf, SCHEMA);
      const enm = root.lookupEnum('Kind');
      assertEqual(enm.values[0], 'OK', 'id 0 -> name');
      assertEqual(enm.values[1], 'OTHER', 'id 1 -> name');
      assertEqual(enm.values.OK, 0, 'name -> id');
      assertEqual(enm.values.OTHER, 1, 'name -> id');
    },
  },
  {
    name: 'a map entry that omits its key stores the default key as data',
    run() {
      const type = parseType(protobuf, SCHEMA, 'Envelope');
      const msg = type.fromText('labels { value { admin: true role: "owner" } }');
      assertOrdinaryShape(msg.labels, 'labels');
      assertOwnData(msg.labels, '', undefined, 'labels');
      assertEqual(msg.labels[''].admin, true, 'value under the default key');
    },
  },
  {
    name: 'a singular field named constructor is stored as ordinary data',
    run() {
      const type = parseType(protobuf, 'syntax="proto3"; message M { string constructor = 1; }', 'M');
      const msg = type.fromText('constructor: "marker"');
      assertEqual(msg.constructor, 'marker', 'value under the field name');
    },
  },
];
