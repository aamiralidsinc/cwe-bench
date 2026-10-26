'use strict';

/*
 * Runs the project's own browser QUnit suite against the submitted sources, headlessly, with
 * jsdom. The suite files (and QUnit) are pristine copies of the pinned tree kept under
 * tests/functional/project/; the library sources come from the submission.
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = process.env.PRODUCT_ROOT || '/workspace';
const HERE = path.join(__dirname, 'project');

module.exports = async function () {
  const { JSDOM } = require('jsdom');

  const files = [
    path.join(HERE, 'pre_libs.js'),
    path.join(PROJECT_ROOT, 'src', 'punycode.js'),
    path.join(PROJECT_ROOT, 'src', 'IPv6.js'),
    path.join(PROJECT_ROOT, 'src', 'SecondLevelDomains.js'),
    path.join(PROJECT_ROOT, 'src', 'URI.js'),
    path.join(PROJECT_ROOT, 'src', 'URITemplate.js'),
    path.join(HERE, 'qunit.js'),
    path.join(HERE, 'urls.js'),
    path.join(HERE, 'test.js'),
    path.join(HERE, 'test_jim.js'),
    path.join(HERE, 'test_template.js'),
  ];

  const dom = new JSDOM(
    '<!DOCTYPE html><html><body><div id="qunit"></div><div id="qunit-fixture"></div></body></html>',
    { url: 'http://example.test/', runScripts: 'outside-only', pretendToBeVisual: true }
  );
  const w = dom.window;
  // jsdom does not implement scrolling; QUnit's HTML reporter calls it on completion.
  Object.defineProperty(w, 'scrollTo', { value: function () {}, writable: true });

  for (const file of files) {
    w.eval(fs.readFileSync(file, 'utf8'));
  }

  const results = [];
  let n = 0;
  const done = new Promise((resolve) => {
    w.QUnit.testDone((t) => {
      n += 1;
      results.push({
        classname: 'project/' + (t.module || 'root'),
        name: `${t.name} #${n}`,
        precomputed: {
          ok: t.failed === 0,
          message: t.failed === 0 ? undefined
            : `${t.failed} of ${t.total} assertions failed in ${t.module || 'root'} :: ${t.name}`,
        },
      });
    });
    w.QUnit.done((d) => resolve(d));
  });

  // jsdom fires the window load event itself; guard QUnit against being started twice.
  let started = false;
  const originalStart = w.QUnit.start;
  w.QUnit.start = function () {
    if (started) return;
    started = true;
    return originalStart.apply(this, arguments);
  };
  try {
    w.QUnit.load();
  } catch (e) {
    // QUnit's HTML reporter can throw on jsdom-only gaps; testDone/done still report.
  }

  const summary = await done;
  if (!results.length) {
    results.push({
      classname: 'project/harness',
      name: 'the project suite ran',
      precomputed: { ok: false, message: `no test results (${JSON.stringify(summary)})` },
    });
  }
  return results;
};
