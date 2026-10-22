'use strict';
const { runSuite } = require('../support/runner');

const cases = [].concat(
  require('./t1_map_keys'),
  require('./t2_field_names'),
  require('./t3_enum_names'),
  require('./t4_settings'),
  require('./t5_schema_options'),
  require('./t6_merge'),
  require('./t7_descriptors'),
  require('./t8_generated'),
  require('./s1_merge_text'),
  require('./s2_merge_json'),
);

const out = process.env.OUT || '/logs/verifier/security/results.xml';
const fails = runSuite('security', cases, out);
process.exit(fails > 0 ? 1 : 0);
