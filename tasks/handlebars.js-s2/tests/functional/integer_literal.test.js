'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');
const { location, pathNode, program, mustache } = require('../support/documents');

function documentWith(value) {
  return program([
    mustache(pathNode(['echo']), [
      { type: 'BigIntLiteral', value: value, original: value, loc: location() }
    ])
  ]);
}

describe('preservation: integer literal arguments', function() {
  it('passes an integer literal to a helper as an integer', function() {
    const template = Handlebars.compile(
      documentWith('123456789012345678901234567890')
    );
    const out = template(
      {},
      { helpers: { echo: function(value) { return typeof value + ':' + String(value); } } }
    );
    assert.strictEqual(out, 'bigint:123456789012345678901234567890');
  });

  it('accepts a negative integer literal', function() {
    const template = Handlebars.compile(documentWith('-5'));
    const out = template(
      {},
      { helpers: { echo: function(value) { return String(value); } } }
    );
    assert.strictEqual(out, '-5');
  });
});
