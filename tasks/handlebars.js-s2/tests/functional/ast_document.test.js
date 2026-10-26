'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');
const {
  location,
  pathNode,
  program,
  mustache
} = require('../support/documents');

describe('preservation: a document supplied as a syntax tree', function() {
  it('compiles and renders ordinary values, literals and a hash argument', function() {
    const ast = program([
      { type: 'ContentStatement', value: 'Hello ', original: 'Hello ', loc: location() },
      mustache(pathNode(['name']), []),
      { type: 'ContentStatement', value: ' ', original: ' ', loc: location() },
      mustache(
        pathNode(['echo']),
        [
          { type: 'StringLiteral', value: 'a', original: 'a', loc: location() },
          { type: 'NumberLiteral', value: 7, original: 7, loc: location() },
          { type: 'BooleanLiteral', value: true, original: true, loc: location() },
          { type: 'NumberLiteral', value: 2.5, original: 2.5, loc: location() }
        ],
        {
          hash: {
            type: 'Hash',
            pairs: [
              {
                type: 'HashPair',
                key: 'label',
                value: { type: 'StringLiteral', value: 'v', original: 'v', loc: location() }
              }
            ],
            loc: location()
          }
        }
      )
    ]);

    const template = Handlebars.compile(ast);
    const out = template(
      { name: 'world' },
      {
        helpers: {
          echo: function(a, b, c, d, options) {
            return [a, b, c, d, options.hash.label].join('|');
          }
        }
      }
    );

    assert.strictEqual(out, 'Hello world a|7|true|2.5|v');
  });

  it('keeps block parameters bound in a supplied document', function() {
    const ast = program([
      {
        type: 'BlockStatement',
        loc: location(),
        path: pathNode(['each']),
        params: [pathNode(['items'])],
        program: program(
          [mustache(pathNode(['item']), [])],
          { blockParams: ['item'] }
        ),
        inverse: null,
        openStrip: {},
        inverseStrip: {},
        closeStrip: {}
      }
    ]);

    assert.strictEqual(
      Handlebars.compile(ast)({ items: ['a', 'b'] }),
      'ab'
    );
  });
});
