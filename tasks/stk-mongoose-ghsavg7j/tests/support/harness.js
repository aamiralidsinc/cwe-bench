'use strict';

// Shared fixture for the hidden suites. It drives the library through its public API only:
// connections, schemas, models, queries and populate. Expected values are computed here from
// documents the test itself inserts, so a hardened library cannot corrupt the oracle.

const path = require('path');
const assert = require('assert');

const ROOT = process.env.MONGOOSE_ROOT || path.resolve(__dirname, '..', '..');
const mongoose = require(ROOT);

function databaseUri(tag) {
  const base = process.env.MONGOOSE_TEST_URI || 'mongodb://127.0.0.1:27017/mongoose_htests';
  const m = base.match(/^(mongodb:\/\/[^/]+)\/([^?]*)(\?.*)?$/);
  if (!m) {
    return base;
  }
  const suffix = `${m[2]}_${tag}_${process.pid}`;
  return `${m[1]}/${suffix}${m[3] || ''}`;
}

async function open(tag) {
  return mongoose.createConnection(databaseUri(tag)).asPromise();
}

function buildModels(conn, suffix) {
  const childName = `Child_${suffix}`;
  const parentName = `Parent_${suffix}`;
  const C = conn.model(childName, new mongoose.Schema({
    name: String,
    age: Number,
    parent: { type: mongoose.Schema.Types.ObjectId, ref: parentName }
  }));
  const P = conn.model(parentName, new mongoose.Schema({
    name: String,
    note: String,
    child: { type: mongoose.Schema.Types.ObjectId, ref: childName },
    children: [{ type: mongoose.Schema.Types.ObjectId, ref: childName }]
  }));
  C.schema.virtual('vparent', {
    ref: parentName,
    localField: 'parent',
    foreignField: '_id'
  });
  return { P, C };
}

async function seed(P, C) {
  await P.deleteMany({});
  await C.deleteMany({});
  const luke = await C.create({ name: 'Luke', age: 10 });
  const leia = await C.create({ name: 'Leia', age: 10 });
  const literal = await C.create({ name: '$where', age: 99 });
  const anakin = await P.create({
    name: 'Anakin',
    note: '$where',
    child: luke._id,
    children: [luke._id, leia._id, literal._id]
  });
  const ben = await C.create({ name: 'Ben', age: 70, parent: anakin._id });
  return { luke, leia, literal, anakin, ben };
}

async function assertUnchanged(P, C, seeded) {
  assert.strictEqual(await P.countDocuments({}), 1);
  assert.strictEqual(await C.countDocuments({}), 4);
  const parent = await P.findById(seeded.anakin._id).lean();
  assert.ok(parent);
  assert.strictEqual(parent.name, 'Anakin');
  const child = await C.findById(seeded.luke._id).lean();
  assert.ok(child);
  assert.strictEqual(child.name, 'Luke');
}

// A refusal must be a client-side error: the script must not have been sent to the database.
const DATABASE_ERRORS = new Set([
  'MongoServerError',
  'MongoNetworkError',
  'MongoParseError',
  'MongoTopologyClosedError',
  'MongoNotConnectedError',
  'MongoExpiredSessionError',
  'MongoRuntimeError'
]);

function clientRefusal(err) {
  assert.ok(err instanceof Error, `expected a client error, got ${String(err)}`);
  assert.ok(!DATABASE_ERRORS.has(err.name), `script reached the database: ${err.name}: ${err.message}`);
  return true;
}

const SCRIPT = 'return false;';

function functionExpression(body) {
  return {
    $function: {
      body: body || 'function() { return true; }',
      args: [],
      lang: 'js'
    }
  };
}

module.exports = {
  mongoose,
  ROOT,
  SCRIPT,
  open,
  buildModels,
  seed,
  assertUnchanged,
  clientRefusal,
  functionExpression
};
