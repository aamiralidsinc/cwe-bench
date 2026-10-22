'use strict';
// T5 — a member name inside a schema option aggregate is data. It is never
// resolved to a member the aggregate object inherits, and it never pulls an
// inherited function into the stored option value.
const {
  loadApp, assert, assertEqual,
} = require('../support/lib');

const protobuf = loadApp();

const SRC = `syntax = "proto2";
message M {
  option (my.opt) = {
    toString: "to-string-marker"
    constructor: "constructor-marker"
    ordinary: "ordinary-marker"
  };
  optional string f = 1;
}
`;

function storedOption() {
  const root = protobuf.parse(SRC, { keepCase: false }).root;
  const t = root.lookupType('M');
  const parsed = t.parsedOptions || [];
  assert(parsed.length > 0, 'option must be recorded');
  const bag = parsed[0]['(my.opt)'];
  assert(bag != null && typeof bag === 'object', 'aggregate option must be an object');
  return bag;
}

module.exports = [
  {
    name: 'an option aggregate member named toString is stored as the literal',
    run() {
      const bag = storedOption();
      assertEqual(bag.toString, 'to-string-marker', 'aggregate member toString');
    },
  },
  {
    name: 'an option aggregate member named constructor is stored as the literal',
    run() {
      const bag = storedOption();
      assertEqual(bag.constructor, 'constructor-marker', 'aggregate member constructor');
    },
  },
  {
    name: 'an option aggregate member named valueOf is stored as the literal',
    run() {
      const root = protobuf.parse(
        'syntax="proto2"; message M { option (my.opt) = { valueOf: "value-of-marker" }; optional string f = 1; }',
        { keepCase: false },
      ).root;
      const bag = root.lookupType('M').parsedOptions[0]['(my.opt)'];
      assertEqual(bag.valueOf, 'value-of-marker', 'aggregate member valueOf');
    },
  },
];
