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

describe('security: integer literal arguments', function() {
  it('an integer literal whose text is not only an integer must not run that text', function() {
    resetProbe();

    const ast = program([
      mustache(pathNode(['echo']), [
        {
          type: 'BigIntLiteral',
          value: "1n, globalThis.__document_probe_value__ = 1",
          original: '1',
          loc: location()
        }
      ])
    ]);

    attempt(function() {
      const template = Handlebars.compile(ast);
      template({}, { helpers: { echo: function() { return ''; } } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
