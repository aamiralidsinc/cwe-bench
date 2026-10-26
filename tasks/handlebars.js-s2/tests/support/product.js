'use strict';

const path = require('node:path');

// The library under test. The verifier builds it from the submitted sources and
// exposes the same path the application would use. The module is loaded lazily so
// that a submission which cannot be loaded fails tests instead of aborting the run.
const WORKSPACE = process.env.WORKSPACE_DIR || process.env.HB_WORKSPACE || '/workspace';

let loaded = null;

function library() {
  if (!loaded) {
    loaded = require(path.join(WORKSPACE, 'lib'));
  }
  return loaded;
}

const Handlebars = new Proxy(
  {},
  {
    get: function(target, property) {
      return library()[property];
    }
  }
);

module.exports = { Handlebars, WORKSPACE };
