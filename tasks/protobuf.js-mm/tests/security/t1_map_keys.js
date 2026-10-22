'use strict';
// T1 — a map-entry key taken from the wire must become ordinary own data on the
// returned map. It must never reach the prototype the map inherits from, and
// the map keeps the shape an ordinary JavaScript object has.
const {
  loadApp, assert, assertEqual, assertOwnData, assertOrdinaryShape, assertNoLeak,
  snapshotBuiltins, assertBuiltinsClean, parseType, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();

const SCHEMA = `
syntax = "proto3";
message Note { bool admin = 1; string role = 2; }
message Envelope { map<string, Note> labels = 1; map<string, string> tags = 2; }
`;

function envelope() {
  return parseType(protobuf, SCHEMA, 'Envelope');
}

function checkProtoEntry(msg, label) {
  assertOrdinaryShape(msg.labels, label + ' labels map');
  assertOwnData(msg.labels, '__proto__', undefined, label + ' labels map');
  const entry = msg.labels['__proto__'];
  assert(entry != null && typeof entry === 'object', label + ': value under the key must be the entry');
  assertNoLeak(msg.labels, 'admin', label + ' labels map');
  assertNoLeak(msg.labels, 'role', label + ' labels map');
  assert(entry.admin === true, label + ': entry value must be readable under its own key');
  assert(entry.role === 'owner', label + ': second entry field must be readable under its own key');
  const before = snapshotBuiltins();
  assertBuiltinsClean(before, label);
}

module.exports = [
  {
    name: 'map key __proto__ in a braced entry is stored as own data',
    run() {
      const msg = envelope().fromText('labels { key: "__proto__" value { admin: true role: "owner" } }');
      checkProtoEntry(msg, 'braced');
    },
  },
  {
    name: 'map key __proto__ in an angle-bracket entry is stored as own data',
    run() {
      const msg = envelope().fromText('labels < key: "__proto__" value < admin: true role: "owner" > >');
      checkProtoEntry(msg, 'angle');
    },
  },
  {
    name: 'map key __proto__ among ordinary list entries is stored as own data',
    run() {
      const msg = envelope().fromText(
        'labels: [ { key: "plain" value { admin: false } }, { key: "__proto__" value { admin: true role: "owner" } } ]',
      );
      checkProtoEntry(msg, 'list');
      assertOwnData(msg.labels, 'plain', undefined, 'list labels map');
      assert(msg.labels.plain && msg.labels.plain.admin === false, 'list: ordinary entry still present');
    },
  },
  {
    name: 'map key __proto__ with a scalar value is stored as own data',
    run() {
      const msg = envelope().fromText('tags { key: "__proto__" value: "marker" }');
      assertOrdinaryShape(msg.tags, 'scalar tags map');
      assertOwnData(msg.tags, '__proto__', 'marker', 'scalar tags map');
    },
  },
  {
    name: 'parsing a __proto__ map key leaves shared built-ins untouched',
    run() {
      const before = snapshotBuiltins();
      const msg = envelope().fromText('labels { key: "__proto__" value { admin: true role: "owner" } }');
      assertBuiltinsClean(before, 'text-format map parse');
      assert(hasOwn(msg.labels, '__proto__'), 'entry must be own data');
    },
  },
  {
    name: 'a map key of __proto__ does not surface the entry as properties of the map',
    run() {
      const msg = envelope().fromText('labels { key: "__proto__" value { admin: true role: "owner" } }');
      assertNoLeak(msg.labels, 'admin', 'braced labels map');
      assertNoLeak(msg.labels, 'role', 'braced labels map');
    },
  },
];
