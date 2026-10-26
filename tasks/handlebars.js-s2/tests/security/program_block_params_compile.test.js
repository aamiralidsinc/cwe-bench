'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');
const {
  resetProbe,
  probeRan,
  location,
  pathNode,
  program,
  attempt
} = require('../support/documents');

describe('security: program block parameter metadata', function() {
  it('a block program whose parameter count is text must not run that text', function() {
    resetProbe();

    const ast = program([
      {
        type: 'BlockStatement',
        loc: location(),
        path: pathNode(['if']),
        params: [{ type: 'BooleanLiteral', value: true, original: true, loc: location() }],
        program: program([], {
          blockParams: { length: "globalThis.__document_probe_value__ = 'block-params'" }
        }),
        inverse: null,
        openStrip: {},
        inverseStrip: {},
        closeStrip: {}
      }
    ]);

    attempt(function() {
      const template = Handlebars.compile(ast);
      template({}, { helpers: { if: function(cond, options) { return options.fn(this); } } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
