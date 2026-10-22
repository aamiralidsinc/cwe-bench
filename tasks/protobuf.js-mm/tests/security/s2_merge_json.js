'use strict';
// S2 — merging a JSON message into an object the caller already holds follows
// the same rule as parsing one: a map-entry key is ordinary own data on the map
// the merge writes, and the map keeps an ordinary shape.
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

// Built with JSON.parse so "__proto__" is an own property of the input, not a
// prototype assignment in a JavaScript literal. The ordinary entry carries a
// non-default field so the merge is expected to keep it.
function jsonInput() {
  return JSON.parse('{"labels":{"__proto__":{"admin":true,"role":"owner"},"plain":{"role":"ordinary"}},"tags":{"__proto__":"marker"}}');
}

function checkMerged(target, label) {
  assert(target.labels != null, label + ': merge must populate the map field');
  assertOrdinaryShape(target.labels, label + ' labels map');
  assertOwnData(target.labels, '__proto__', undefined, label + ' labels map');
  const entry = target.labels['__proto__'];
  assert(entry && entry.admin === true, label + ': entry readable under its own key');
  assertNoLeak(target.labels, 'admin', label + ' labels map');
}

module.exports = [
  {
    name: 'merge from JSON stores a __proto__ map key as own data',
    run() {
      const target = {};
      envelope().mergeFromJson(target, jsonInput());
      checkMerged(target, 'labels');
    },
  },
  {
    name: 'merge from JSON stores a __proto__ scalar map key as own data',
    run() {
      const target = {};
      envelope().mergeFromJson(target, jsonInput());
      assert(target.tags != null, 'merge must populate the map field');
      assertOwnData(target.tags, '__proto__', 'marker', 'merged tags map');
      assertOrdinaryShape(target.tags, 'merged tags map');
    },
  },
  {
    name: 'merge from JSON keeps ordinary entries next to a __proto__ key',
    run() {
      const target = {};
      envelope().mergeFromJson(target, jsonInput());
      checkMerged(target, 'labels');
      assertOwnData(target.labels, 'plain', undefined, 'merged labels map');
      assert(target.labels.plain && target.labels.plain.role === 'ordinary', 'ordinary entry still present');
    },
  },
  {
    name: 'merge from JSON leaves shared built-ins untouched',
    run() {
      const before = snapshotBuiltins();
      const target = {};
      envelope().mergeFromJson(target, jsonInput());
      assertBuiltinsClean(before, 'merge from JSON');
      assert(hasOwn(target.labels, '__proto__'), 'entry must be own data');
    },
  },
];
