'use strict';
const { runSuite } = require('../support/runner');

const cases = [].concat(
  require('./ordinary'),
  require('./shadow_names'),
  require('./settings_merge'),
  require('./descriptors_generated'),
  require('./project_tests'),
);

const out = process.env.OUT || '/logs/verifier/functional/results.xml';
const fails = runSuite('functional', cases, out);
process.exit(fails > 0 ? 1 : 0);
