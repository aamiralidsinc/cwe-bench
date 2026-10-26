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

describe('security: integer literal arguments, eager compilation', function() {
  it('the prepared specification must not carry integer-literal text', function() {
    resetProbe();

    const ast = program([
      mustache(pathNode(['echo']), [
        {
          type: 'BigIntLiteral',
          value: "2n, globalThis.__document_probe_value__ = 1",
          original: '2',
          loc: location()
        }
      ])
    ]);

    attempt(function() {
      const spec = Handlebars.precompile(ast);
      const template = Handlebars.template(eval('(' + spec + ')'));
      template({}, { helpers: { echo: function() { return ''; } } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
