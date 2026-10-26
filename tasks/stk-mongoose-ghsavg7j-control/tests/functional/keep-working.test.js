'use strict';

const assert = require('assert');
const {
  mongoose,
  open,
  buildModels,
  seed
} = require('../support/harness');

describe('legitimate query use keeps working', function() {
  this.timeout(30000);

  let conn;
  let P;
  let C;
  let Mixed;
  let seeded;

  before(async function() {
    conn = await open('func_keep_working');
    ({ P, C } = buildModels(conn, 'FuncKW'));
    seeded = await seed(P, C);
    Mixed = conn.model('Mixed_FuncKW', new mongoose.Schema({
      label: String,
      data: mongoose.Schema.Types.Mixed
    }));
    await Mixed.deleteMany({});
    await Mixed.create({ label: 'one', data: { keep: 1 } });
    await Mixed.create({ label: 'two', data: { keep: 2 } });
  });

  after(async function() {
    await conn.dropDatabase();
    await conn.close();
  });

  it('keeps direct where queries working', async function() {
    const byModel = await P.$where('return this.name === "Anakin"').exec();
    assert.strictEqual(byModel.length, 1);
    assert.strictEqual(byModel[0].name, 'Anakin');
    const byQuery = await P.find().$where('return this.name === "Anakin"').exec();
    assert.strictEqual(byQuery.length, 1);
    assert.strictEqual(byQuery[0].name, 'Anakin');
  });

  it('keeps populate without a filter working', async function() {
    const parents = await P.find().populate('child').exec();
    assert.strictEqual(parents.length, 1);
    assert.ok(parents[0].child);
    assert.strictEqual(parents[0].child.name, 'Luke');
  });

  it('keeps logical operators in populate filters working', async function() {
    const or = await P.find().populate({
      path: 'children',
      match: { $or: [{ name: 'Luke' }, { name: 'Leia' }] }
    }).exec();
    assert.deepStrictEqual(or[0].children.map(c => c.name).sort(), ['Leia', 'Luke']);

    const and = await P.find().populate({
      path: 'children',
      match: { $and: [{ age: 10 }] }
    }).exec();
    assert.deepStrictEqual(and[0].children.map(c => c.name).sort(), ['Leia', 'Luke']);

    const nor = await P.find().populate({
      path: 'children',
      match: { $nor: [{ name: 'Luke' }] }
    }).exec();
    assert.deepStrictEqual(nor[0].children.map(c => c.name).sort(), ['$where', 'Leia']);
  });

  it('keeps expression comparisons in populate filters working', async function() {
    const parents = await P.find().populate({
      path: 'child',
      match: { $expr: { $eq: ['$age', 10] } }
    }).exec();
    assert.ok(parents[0].child);
    assert.strictEqual(parents[0].child.name, 'Luke');
  });

  it('keeps match functions and single-element filter lists working', async function() {
    const fromFunction = await P.find().populate({
      path: 'child',
      match: () => ({ name: 'Luke' })
    }).exec();
    assert.ok(fromFunction[0].child);
    assert.strictEqual(fromFunction[0].child.name, 'Luke');

    const fromList = await P.find().populate({
      path: 'child',
      match: [{ name: 'Luke' }]
    }).exec();
    assert.ok(fromList[0].child);
    assert.strictEqual(fromList[0].child.name, 'Luke');
  });

  it('keeps a plain value that looks like an operator as a plain value', async function() {
    const parents = await P.find().populate({
      path: 'children',
      match: { name: '$where' }
    }).exec();
    assert.deepStrictEqual(parents[0].children.map(c => c.name), ['$where']);
  });

  it('keeps sanitised filters wrapping operator values', async function() {
    const sanitised = await Mixed.find({ data: { $ne: null } })
      .setOptions({ sanitizeFilter: true })
      .exec();
    assert.strictEqual(sanitised.length, 0);
    const plain = await Mixed.find({ data: { $ne: null } }).exec();
    assert.strictEqual(plain.length, 2);
  });

  it('keeps sanitised filters handling logical operators', async function() {
    const and = await Mixed.find({ $and: [{ data: { $ne: null } }] })
      .setOptions({ sanitizeFilter: true })
      .exec();
    assert.strictEqual(and.length, 0);
    const or = await Mixed.find({ $or: [{ data: { $ne: null } }] })
      .setOptions({ sanitizeFilter: true })
      .exec();
    assert.strictEqual(or.length, 0);
  });

  it('keeps explicitly trusted values passing through the sanitiser', async function() {
    const trusted = await Mixed.find({ data: mongoose.trusted({ $ne: null }) })
      .setOptions({ sanitizeFilter: true })
      .exec();
    assert.strictEqual(trusted.length, 2);
  });
});
