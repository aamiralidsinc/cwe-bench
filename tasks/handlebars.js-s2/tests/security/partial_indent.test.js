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

describe('security: partial indentation written into generated code', function() {
  it('indentation text carried by a partial must not run as code', function() {
    resetProbe();

    const ast = program([
      {
        type: 'ContentStatement',
        value: 'x',
        original: 'x',
        loc: location()
      },
      {
        type: 'PartialStatement',
        loc: location(),
        name: pathNode(['ph']),
        params: [],
        indent: '", "probe": globalThis.__document_probe_value__ = \'partial-indent\', "x": "',
        strip: { open: false, close: false }
      }
    ]);

    attempt(function() {
      const template = Handlebars.compile(ast);
      template({}, { partials: { ph: 'P' } });
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
