'use strict';
// S1 — merging a text-format message into an object the caller already holds
// follows the same rule as parsing one: a map-entry key is ordinary own data on
// the map the merge writes, and the map keeps an ordinary shape.
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
    name: 'merge from text stores a __proto__ map key as own data',
    run() {
      const target = {};
      envelope().mergeFromText(target, 'labels { key: "__proto__" value { admin: true role: "owner" } }');
      checkMerged(target, 'braced');
    },
  },
  {
    name: 'merge from text stores a __proto__ map key in the angle form as own data',
    run() {
      const target = {};
      envelope().mergeFromText(target, 'labels < key: "__proto__" value < admin: true role: "owner" > >');
      checkMerged(target, 'angle');
    },
  },
  {
    name: 'merge from text stores a __proto__ scalar map key as own data',
    run() {
      const target = {};
      envelope().mergeFromText(target, 'tags { key: "__proto__" value: "marker" }');
      assert(target.tags != null, 'merge must populate the map field');
      assertOwnData(target.tags, '__proto__', 'marker', 'merged tags map');
      assertOrdinaryShape(target.tags, 'merged tags map');
    },
  },
  {
    name: 'merge from text keeps ordinary entries next to a __proto__ key',
    run() {
      const target = {};
      envelope().mergeFromText(
        target,
        'labels: [ { key: "plain" value { admin: false } }, { key: "__proto__" value { admin: true } } ]',
      );
      checkMerged(target, 'list');
      assertOwnData(target.labels, 'plain', undefined, 'merged labels map');
      assert(target.labels.plain && target.labels.plain.admin === false, 'ordinary entry still present');
    },
  },
  {
    name: 'merge from text leaves shared built-ins untouched',
    run() {
      const before = snapshotBuiltins();
      const target = {};
      envelope().mergeFromText(target, 'labels { key: "__proto__" value { admin: true } }');
      assertBuiltinsClean(before, 'merge from text');
      // and the entry is still data, not a prototype replacement
      assert(hasOwn(target.labels, '__proto__'), 'entry must be own data');
    },
  },
];
