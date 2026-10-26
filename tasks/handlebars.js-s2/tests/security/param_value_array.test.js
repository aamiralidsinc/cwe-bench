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

describe('security: literal parameter values in string-parameter mode', function() {
  it('a string argument whose value is a list must not be printed as code', function() {
    resetProbe();

    const ast = program([
      mustache(pathNode(['echo']), [
        {
          type: 'StringLiteral',
          value: ["globalThis.__document_probe_value__ = 'param-value'"],
          original: 'x',
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
