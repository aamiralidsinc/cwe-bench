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

describe('populated lookups refuse a top-level server-side script', function() {
  this.timeout(30000);

  let conn;
  let P;
  let C;
  let seeded;

  before(async function() {
    conn = await open('ctl_populate_where');
    ({ P, C } = buildModels(conn, 'CtlPW'));
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

  it('refuses a script at the top level of a findOne populate filter', async function() {
    await assert.rejects(
      () => P.findOne().populate({ path: 'child', match: { $where: SCRIPT } }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });

  it('refuses a script in an array of populate filters', async function() {
    await refuse([{ $where: SCRIPT }]);
  });

  it('refuses a script returned by a match function', async function() {
    await refuse(() => ({ $where: SCRIPT }));
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
