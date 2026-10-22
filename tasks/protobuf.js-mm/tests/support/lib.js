'use strict';
// Shared helpers. The product is loaded from $APP (the tree the agent edited).
// Expectations are written here as plain data checks.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const APP = process.env.APP || process.env.APP_DIR || '/app';

function loadApp() {
  // Fresh module registry per suite so one suite cannot see another's types.
  const protobuf = require(path.join(APP, 'index.js'));
  const textformat = require(path.join(APP, 'ext', 'textformat.js'));
  const protojson = require(path.join(APP, 'ext', 'protojson.js'));
  require(path.join(APP, 'ext', 'descriptor.js'));
  if (typeof textformat.install === 'function') textformat.install();
  if (typeof protojson.install === 'function') protojson.install();
  return protobuf;
}

function descriptorOf(protobuf) {
  require(path.join(APP, 'ext', 'descriptor.js'));
  return protobuf.descriptor;
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg || 'assertion failed');
}

function assertEqual(actual, expected, msg) {
  if (actual !== expected) {
    throw new Error(
      (msg || 'values differ') + '\n  expected: ' + inspect(expected) + '\n  actual:   ' + inspect(actual),
    );
  }
}

function inspect(v) {
  try {
    return typeof v === 'function'
      ? '[Function ' + (v.name || 'anonymous') + ']'
      : JSON.stringify(v);
  } catch (e) {
    return String(v);
  }
}

function hasOwn(obj, key) {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

// Snapshot of the own property names every shared built-in currently has, so a
// test can prove the library did not modify one.
function snapshotBuiltins() {
  const names = [
    'Object', 'Function', 'Array', 'String', 'Number', 'Boolean', 'RegExp', 'Error',
    'TypeError', 'RangeError', 'SyntaxError', 'JSON', 'Math', 'Date',
  ];
  const out = {};
  for (const n of names) {
    const g = globalThis[n];
    if (!g) continue;
    out[n] = {
      self: Object.getOwnPropertyNames(g).slice().sort().join(','),
      proto: Object.getOwnPropertyNames(Object.getPrototypeOf(g) || {}).slice().sort().join(','),
    };
  }
  out.ObjectPrototype = Object.getOwnPropertyNames(Object.prototype).slice().sort().join(',');
  return out;
}

function assertBuiltinsClean(before, label) {
  const after = snapshotBuiltins();
  for (const k of Object.keys(before)) {
    if (before[k].self !== after[k].self) {
      throw new Error(
        (label || 'library') + ' modified shared built-in ' + k + '\n  before: ' + before[k].self +
        '\n  after:  ' + after[k].self,
      );
    }
  }
  if (before.ObjectPrototype !== after.ObjectPrototype) {
    throw new Error(
      (label || 'library') + ' modified Object.prototype\n  before: ' + before.ObjectPrototype +
      '\n  after:  ' + after.ObjectPrototype,
    );
  }
}

// Run fn, require it to throw, and require that no shared built-in changed.
function assertClientError(fn, label) {
  const before = snapshotBuiltins();
  let threw = null;
  try {
    fn();
  } catch (e) {
    threw = e;
  }
  assertBuiltinsClean(before, label);
  assert(threw, (label || 'call') + ' must be rejected with an error');
  return threw;
}

// A name the library treated as data must be an own, enumerable key whose value
// is readable under that key — not a hole punched through the prototype.
function assertOwnData(obj, key, expected, label) {
  const where = label || 'container';
  assert(obj != null && typeof obj === 'object', where + ': expected an object, got ' + inspect(obj));
  assert(hasOwn(obj, key), where + ': name ' + inspect(key) + ' is not stored as own data');
  const desc = Object.getOwnPropertyDescriptor(obj, key);
  assert(desc && desc.enumerable, where + ': name ' + inspect(key) + ' is not enumerable data');
  const actual = obj[key];
  if (expected !== undefined) {
    assertEqual(actual, expected, where + ': value under ' + inspect(key));
  }
  return actual;
}

// The container keeps the shape an ordinary JavaScript object has. A null-
// prototype bag is not the same shape.
function assertOrdinaryShape(obj, label) {
  const where = label || 'container';
  assert(obj != null && typeof obj === 'object', where + ': expected an object, got ' + inspect(obj));
  const proto = Object.getPrototypeOf(obj);
  assert(
    proto === Object.prototype,
    where + ': map must keep Object.prototype as its prototype, got ' +
      (proto === null ? 'null (bare container)' : (proto.constructor && proto.constructor.name) || 'other'),
  );
}

// The attack value must not appear as a property of the container itself.
function assertNoLeak(obj, key, label) {
  const where = label || 'container';
  assert(!hasOwn(obj, key), where + ': leaked ' + inspect(key) + ' onto the container');
  assert(obj[key] === undefined, where + ': ' + inspect(key) + ' is readable from the container');
}

function parseType(protobuf, protoSource, typeName) {
  const root = protobuf.parse(protoSource, { keepCase: false }).root.resolveAll();
  return root.lookupType(typeName);
}

function parseRoot(protobuf, protoSource) {
  return protobuf.parse(protoSource, { keepCase: false }).root.resolveAll();
}

function tmpFile(name, contents) {
  const p = path.join(os.tmpdir(), 'pjs-verifier-' + process.pid + '-' + name);
  fs.writeFileSync(p, contents);
  return p;
}

// Run the CLI code generator on a .proto and evaluate the emitted module,
// returning its $root namespace. The generator only produces the module under
// test; every expectation is computed here as a plain data check.
function pbjsStatic(protobuf, protoSource) {
  const protoPath = tmpFile(Date.now() + '-' + Math.random().toString(36).slice(2) + '.proto', protoSource);
  const pbjs = path.join(APP, 'cli', 'bin', 'pbjs');
  const src = execFileSync(process.execPath, [pbjs, '-t', 'static', protoPath], {
    encoding: 'utf8',
    cwd: APP,
    env: {
      ...process.env,
      NODE_PATH: path.join(APP, 'node_modules') + (process.env.NODE_PATH ? ':' + process.env.NODE_PATH : ''),
    },
  });
  const fn = new Function('$protobuf', src + '\n;return $root;');
  return fn(protobuf);
}

module.exports = {
  APP,
  loadApp,
  assert,
  assertEqual,
  assertOwnData,
  assertOrdinaryShape,
  assertNoLeak,
  assertBuiltinsClean,
  assertClientError,
  snapshotBuiltins,
  hasOwn,
  inspect,
  parseType,
  parseRoot,
  pbjsStatic,
  descriptorOf,
};
