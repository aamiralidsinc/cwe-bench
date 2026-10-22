'use strict';
// T8 — code the library emits follows the same rules as code it builds at
// runtime. A generated enum table never resolves an inherited member as if it
// were a value.
const {
  loadApp, assert, assertEqual, hasOwn, pbjsStatic,
} = require('../support/lib');

const protobuf = loadApp();

const SRC = `syntax = "proto3";
enum Kind {
  constructor = 0;
  toString = 1;
  OK = 2;
}
`;

function generatedTable() {
  const root = pbjsStatic(protobuf, SRC);
  assert(root && root.Kind, 'generator must emit the enum table');
  return root.Kind;
}

// An undeclared name must not resolve to anything the table inherits. Absent
// and "a number" are both fine; a function or other inherited member is not.
function assertNotInheritedValue(values, name) {
  const v = values[name];
  assert(
    v === undefined || typeof v === 'number',
    'undeclared name ' + name + ' must not resolve to an inherited member, got ' +
      (typeof v === 'function' ? '[Function ' + (v.name || '') + ']' : String(v)),
  );
}

module.exports = [
  {
    name: 'a generated enum table never reports hasOwnProperty as a value',
    run() {
      assertNotInheritedValue(generatedTable(), 'hasOwnProperty');
    },
  },
  {
    name: 'a generated enum table never reports valueOf as a value',
    run() {
      assertNotInheritedValue(generatedTable(), 'valueOf');
    },
  },
  {
    name: 'a generated enum table never reports isPrototypeOf as a value',
    run() {
      assertNotInheritedValue(generatedTable(), 'isPrototypeOf');
    },
  },
  {
    name: 'a generated enum table never reports propertyIsEnumerable as a value',
    run() {
      assertNotInheritedValue(generatedTable(), 'propertyIsEnumerable');
    },
  },
  {
    name: 'a generated enum table never reports toLocaleString as a value',
    run() {
      assertNotInheritedValue(generatedTable(), 'toLocaleString');
    },
  },
];
