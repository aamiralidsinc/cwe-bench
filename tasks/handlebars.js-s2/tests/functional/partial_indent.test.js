'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');
const { location, pathNode, program } = require('../support/documents');

describe('preservation: partial indentation', function() {
  it('keeps the indentation of a parsed standalone partial', function() {
    const template = Handlebars.compile('  {{> ph}}\n');
    assert.strictEqual(
      template({}, { partials: { ph: 'one\ntwo\n' } }),
      '  one\n  two\n'
    );
  });

  it('keeps a supplied indentation of spaces and tabs', function() {
    const ast = program([
      {
        type: 'ContentStatement',
        value: 'x\n',
        original: 'x\n',
        loc: location()
      },
      {
        type: 'PartialStatement',
        loc: location(),
        name: pathNode(['ph']),
        params: [],
        indent: '  ',
        strip: { open: false, close: false }
      }
    ]);
    assert.strictEqual(
      Handlebars.compile(ast)({}, { partials: { ph: 'one\ntwo\n' } }),
      'x\n  one\n  two\n'
    );
  });
});
