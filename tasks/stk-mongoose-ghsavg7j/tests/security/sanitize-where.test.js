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

describe('sanitised filters refuse server-side scripts', function() {
  this.timeout(30000);

  let conn;
  let P;
  let C;
  let seeded;

  before(async function() {
    conn = await open('sec_sanitize_where');
    ({ P, C } = buildModels(conn, 'SecSW'));
    seeded = await seed(P, C);
  });

  after(async function() {
    await conn.dropDatabase();
    await conn.close();
  });

  it('refuses a script in a filter the caller asked to sanitise', async function() {
    await assert.rejects(
      () => P.find({ $where: SCRIPT }).setOptions({ sanitizeFilter: true }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });

  it('refuses a script nested in a logical operator in a sanitised filter', async function() {
    await assert.rejects(
      () => P.find({ $nor: [{ $where: SCRIPT }] }).setOptions({ sanitizeFilter: true }).exec(),
      clientRefusal
    );
    await assert.rejects(
      () => P.find({ $or: [{ $where: SCRIPT }] }).setOptions({ sanitizeFilter: true }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });

  it('refuses a script in a sanitised findOne filter', async function() {
    await assert.rejects(
      () => P.findOne({ $where: SCRIPT }).setOptions({ sanitizeFilter: true }).exec(),
      clientRefusal
    );
    await assertUnchanged(P, C, seeded);
  });

  it('refuses a script when sanitising is enabled on the connection', async function() {
    conn.set('sanitizeFilter', true);
    try {
      await assert.rejects(
        () => P.find({ $where: SCRIPT }).exec(),
        clientRefusal
      );
      await assert.rejects(
        () => P.find({ $nor: [{ $where: SCRIPT }] }).exec(),
        clientRefusal
      );
    } finally {
      delete conn.options.sanitizeFilter;
    }
    await assertUnchanged(P, C, seeded);
  });
});
