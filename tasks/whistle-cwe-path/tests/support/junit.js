// Minimal async test registry that emits a JUnit XML file. No framework
// dependency, so a hardened product cannot pull a test runner out from under us.
'use strict';
var fs = require('fs');
var path = require('path');

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function Suite(name) {
  this.name = name;
  this.cases = [];
}

// fn(ctx-free): receives (done); call done() on success or done(err) on failure.
Suite.prototype.test = function (name, fn) {
  this.cases.push({ name: name, fn: fn });
};

Suite.prototype.run = function (outFile) {
  var self = this;
  var results = [];
  var i = 0;
  function finish() {
    var failures = results.filter(function (r) { return !r.ok; }).length;
    var xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<testsuite name="' + esc(self.name) + '" tests="' + results.length +
           '" failures="' + failures + '">\n';
    results.forEach(function (r) {
      xml += '  <testcase classname="' + esc(self.name) + '" name="' + esc(r.name) + '">';
      if (!r.ok) {
        xml += '\n    <failure message="' + esc(r.msg || 'failed') + '">' +
               esc(r.detail || '') + '</failure>\n  ';
      }
      xml += '</testcase>\n';
    });
    xml += '</testsuite>\n';
    fs.mkdirSync(path.dirname(outFile), { recursive: true });
    fs.writeFileSync(outFile, xml);
    // The product boots background timers; exit explicitly once results are written.
    process.exit(0);
  }
  function next() {
    if (i >= self.cases.length) {
      return finish();
    }
    var c = self.cases[i++];
    var settled = false;
    var guard = setTimeout(function () {
      if (settled) { return; }
      settled = true;
      results.push({ name: c.name, ok: false, msg: 'timeout', detail: 'case did not finish in time' });
      next();
    }, 15000);
    function done(err) {
      if (settled) { return; }
      settled = true;
      clearTimeout(guard);
      if (err) {
        results.push({ name: c.name, ok: false, msg: String(err && err.message || err),
                       detail: String(err && err.stack || err) });
      } else {
        results.push({ name: c.name, ok: true });
      }
      next();
    }
    try {
      c.fn(done);
    } catch (e) {
      done(e);
    }
  }
  next();
};

module.exports = { Suite: Suite };
