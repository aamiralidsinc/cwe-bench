'use strict';

const assert = require('assert');
const {
  SCRIPT,
  open,
  buildModels,
  seed,
  assertUnchanged,
  clientRefusal
} = require('../support/harness');

describe('populated lookups refuse server-side scripts', function() {
  this.timeout(30000);

  let conn;
  let P;
  let C;
  let seeded;

  before(async function() {
    conn = await open('sec_populate_where');
    ({ P, C } = buildModels(conn, 'SecPW'));
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

  it('refuses a script at the top level of a populate filter', async function() {
    await refuse({ $where: SCRIPT });
  });

  it('refuses a script nested in an or filter', async function() {
    await refuse({ $or: [{ $where: SCRIPT }] });
  });

  it('refuses a script nested in an and filter', async function() {
    await refuse({ $and: [{ $where: SCRIPT }] });
  });

  it('refuses a script nested in a nor filter', async function() {
    await refuse({ $nor: [{ $where: SCRIPT }] });
  });

  it('refuses a script in an array of populate filters', async function() {
    await refuse([{ $where: SCRIPT }]);
  });

  it('refuses a script returned by a match function', async function() {
    await refuse(() => ({ $where: SCRIPT }));
  });

  it('refuses a script nested in a filter returned by a match function', async function() {
    await refuse(() => ({ $or: [{ $where: SCRIPT }] }));
  });

  it('refuses a script in a virtual populate filter', async function() {
    await assert.rejects(
      () => C.find().populate({ path: 'vparent', match: { $where: SCRIPT } }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });

  it('refuses a script nested in a virtual populate filter', async function() {
    await assert.rejects(
      () => C.find().populate({ path: 'vparent', match: { $or: [{ $where: SCRIPT }] } }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });

  it('refuses a script when a document is populated directly', async function() {
    const parent = await P.findById(seeded.anakin._id).exec();
    await assert.rejects(
      () => parent.populate({ path: 'child', match: { $where: SCRIPT } }),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });
});
