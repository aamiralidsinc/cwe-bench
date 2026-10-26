'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');
const {
  resetProbe,
  probeRan,
  location,
  pathNode,
  program,
  mustache,
  attempt
} = require('../support/documents');

describe('security: parameter context depth in string-parameter mode', function() {
  it('a literal argument that carries a text depth must not emit that text', function() {
    resetProbe();

    const ast = program([
      mustache(pathNode(['echo']), [
        {
          type: 'NumberLiteral',
          value: 1,
          original: 1,
          depth: "globalThis.__document_probe_value__ = 'param-depth'",
          loc: location()
        }
      ])
    ]);

    attempt(function() {
      const template = Handlebars.compile(ast, { stringParams: true });
      template({}, { helpers: { echo: function() { return ''; } } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
