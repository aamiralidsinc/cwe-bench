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

describe('security: parameter context depth, eager compilation', function() {
  it('a text depth on a string argument must not reach the prepared specification', function() {
    resetProbe();

    const ast = program([
      mustache(pathNode(['echo']), [
        {
          type: 'StringLiteral',
          value: 'x',
          original: 'x',
          depth: "globalThis.__document_probe_value__ = 'param-depth-eager'",
          loc: location()
        }
      ])
    ]);

    attempt(function() {
      const spec = Handlebars.precompile(ast, { stringParams: true });
      const template = Handlebars.template(eval('(' + spec + ')'));
      template({}, { helpers: { echo: function() { return ''; } } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
