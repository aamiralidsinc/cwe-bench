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

const options = {};

function viaCompilerStages(ast, runtimeOptions) {
  const environment = new Handlebars.Compiler().compile(ast, options);
  const specification = new Handlebars.JavaScriptCompiler().compile(
    environment,
    options
  );
  const template = Handlebars.template(eval('(' + specification + ')'));
  template({}, runtimeOptions);
}

describe('security: separate compiler stages', function() {
  it('a text path depth must not be emitted when the stages are used directly', function() {
    resetProbe();

    const ast = program([
      mustache(
        pathNode(['name'], {
          depth: "globalThis.__document_probe_value__ = 'stage-depth'"
        }),
        []
      )
    ]);

    attempt(function() {
      viaCompilerStages(ast, {});
    });

    assert.strictEqual(probeRan(), false, 'document text ran as code');
  });
});
