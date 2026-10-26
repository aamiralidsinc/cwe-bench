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

const options = {};

function viaCompilerStages(ast) {
  const environment = new Handlebars.Compiler().compile(ast, options);
  const specification = new Handlebars.JavaScriptCompiler().compile(
    environment,
    options
  );
  const template = Handlebars.template(eval('(' + specification + ')'));
  template({}, {});
}

describe('security: separate compiler stages, block metadata', function() {
  it('a text parameter count must not be emitted when the stages are used directly', function() {
    resetProbe();

    const ast = program([
      {
        type: 'BlockStatement',
        loc: location(),
        path: pathNode(['each']),
        params: [pathNode(['items'])],
        program: program([], {
          blockParams: { length: "globalThis.__document_probe_value__ = 'stage-block-params'" }
        }),
        inverse: null,
        openStrip: {},
        inverseStrip: {},
        closeStrip: {}
      }
    ]);

    attempt(function() {
      viaCompilerStages(ast);
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
