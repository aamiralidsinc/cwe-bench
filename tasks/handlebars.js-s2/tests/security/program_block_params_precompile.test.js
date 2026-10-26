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

describe('security: program block parameter metadata, eager compilation', function() {
  it('a prepared template specification must not carry the parameter-count text', function() {
    resetProbe();

    const ast = program([
      {
        type: 'BlockStatement',
        loc: location(),
        path: pathNode(['each']),
        params: [pathNode(['items'])],
        program: program([], {
          blockParams: { length: "globalThis.__document_probe_value__ = 'block-params-eager'" }
        }),
        inverse: null,
        openStrip: {},
        inverseStrip: {},
        closeStrip: {}
      }
    ]);

    attempt(function() {
      const spec = Handlebars.precompile(ast);
      const template = Handlebars.template(eval('(' + spec + ')'));
      template({ items: [1] });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
