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

describe('security: parameter source text in string-parameter mode', function() {
  it('a path argument whose source text is a list must not be printed as code', function() {
    resetProbe();

    const ast = program([
      mustache(pathNode(['echo']), [
        pathNode([], {
          original: ["globalThis.__document_probe_value__ = 'param-original'"]
        })
      ])
    ]);

    attempt(function() {
      const template = Handlebars.compile(ast, { stringParams: true });
      template({}, { helpers: { echo: function() { return ''; } } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
