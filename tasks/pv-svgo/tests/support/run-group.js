'use strict';

// Tiny JUnit-XML reporter so the hidden groups can run under plain Node with no extra dependency.
// Usage: node run-group.js <test-dir> <out.xml>

const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');

const [, , dirArg, outArg] = process.argv;
if (!dirArg || !outArg) {
  console.error('usage: run-group.js <test-dir> <out.xml>');
  process.exit(2);
}

const dir = path.resolve(dirArg);
const files = fs
  .readdirSync(dir)
  .filter((name) => name.endsWith('.test.js'))
  .sort();

const results = [];

const record = (classname, name, fn) => {
  const started = performance.now();
  try {
    const value = fn();
    if (value && typeof value.then === 'function') {
      throw new Error('tests must be synchronous');
    }
    results.push({ classname, name, status: 'pass', ms: performance.now() - started });
  } catch (error) {
    const message = error && error.stack ? String(error.stack) : String(error);
    results.push({
      classname,
      name,
      status: 'fail',
      ms: performance.now() - started,
      message,
    });
  }
};

for (const file of files) {
  const classname = path.basename(file, '.test.js');
  let module_;
  try {
    module_ = require(path.join(dir, file));
  } catch (error) {
    record(classname, file, () => {
      throw error;
    });
    continue;
  }
  const tests = Array.isArray(module_) ? module_ : module_ && module_.tests;
  if (!Array.isArray(tests)) {
    record(classname, file, () => {
      throw new Error('test module must export an array or { tests: [...] }');
    });
    continue;
  }
  for (const test of tests) {
    if (!test || typeof test.name !== 'string' || typeof test.fn !== 'function') {
      record(classname, file, () => {
        throw new Error('each test needs a string name and a function fn');
      });
      continue;
    }
    record(classname, test.name, test.fn);
  }
}

const escape = (text) =>
  String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
    // strip characters that are not valid in XML 1.0
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '');

const failures = results.filter((r) => r.status === 'fail').length;
let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
xml += `<testsuite name="${escape(path.basename(dir))}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">\n`;
for (const result of results) {
  xml += `  <testcase classname="${escape(result.classname)}" name="${escape(result.name)}" time="${(result.ms / 1000).toFixed(4)}"`;
  if (result.status === 'pass') {
    xml += '/>\n';
  } else {
    xml += `>\n    <failure message="${escape(result.message.split('\n')[0].slice(0, 500))}">${escape(result.message)}</failure>\n  </testcase>\n`;
  }
}
xml += '</testsuite>\n';

fs.mkdirSync(path.dirname(path.resolve(outArg)), { recursive: true });
fs.writeFileSync(outArg, xml);
console.log(
  `${path.basename(dir)}: ${results.length - failures}/${results.length} passed` +
    (failures ? `, ${failures} failed` : ''),
);
process.exit(0);
