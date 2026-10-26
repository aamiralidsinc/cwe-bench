'use strict';

const assert = require('assert');
const {
  open,
  buildModels,
  seed,
  assertUnchanged,
  clientRefusal,
  functionExpression
} = require('../support/harness');

describe('populated lookups refuse function expressions', function() {
  this.timeout(30000);

  let conn;
  let P;
  let C;
  let seeded;

  before(async function() {
    conn = await open('sec_populate_function');
    ({ P, C } = buildModels(conn, 'SecPF'));
    seeded = await seed(P, C);
  });

  after(async function() {
    await conn.dropDatabase();
    await conn.close();
  });

  async function refuse(match) {
    await assert.rejects(
      () => P.find().populate({ path: 'child', match }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  }

  it('refuses a function expression in a populate filter', async function() {
    await refuse({ $expr: functionExpression() });
  });

  it('refuses a function expression nested in an or filter', async function() {
    await refuse({ $or: [{ $expr: functionExpression() }] });
  });

  it('refuses a function expression nested in an and filter', async function() {
    await refuse({ $and: [{ $expr: functionExpression() }] });
  });

  it('refuses a function expression used as an expression operand', async function() {
    await refuse({ $expr: { $eq: [functionExpression(), 1] } });
  });

  it('refuses a function expression nested in a virtual populate filter', async function() {
    await assert.rejects(
      () => C.find().populate({ path: 'vparent', match: { $expr: functionExpression() } }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });
});
