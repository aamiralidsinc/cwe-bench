#!/usr/bin/env node
"use strict";
// Runs every *.js file in one test group and writes JUnit XML.
//   node run_group.js <security|functional> <output.xml>

var fs = require("fs");
var path = require("path");

var group = process.argv[2];
var outFile = process.argv[3];
if (!group || !outFile) {
    console.error("usage: run_group.js <group> <output.xml>");
    process.exit(2);
}

var harness = require(path.join(__dirname, "support", "harness.js"));
var dir = path.join(__dirname, group);
var files = fs.readdirSync(dir).filter(function (f) {
    return f.slice(-3) === ".js";
}).sort();

files.forEach(function (f) {
    try {
        require(path.join(dir, f));
    } catch (e) {
        harness.test(f + " (failed to load)", function () {
            throw e;
        });
    }
});

var results = [];
harness.list().forEach(function (t) {
    try {
        t.fn();
        results.push({ name: t.name, ok: true });
    } catch (e) {
        results.push({
            name: t.name,
            ok: false,
            message: (e && e.stack ? e.stack : String(e)).split("\n").slice(0, 12).join("\n")
        });
    }
});

function xmlEscape(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&apos;");
}

var failures = results.filter(function (r) { return !r.ok; }).length;
var lines = [];
lines.push('<?xml version="1.0" encoding="UTF-8"?>');
lines.push('<testsuite name="' + xmlEscape(group) + '" tests="' + results.length +
    '" failures="' + failures + '" errors="0" skipped="0" time="0">');
results.forEach(function (r) {
    lines.push('  <testcase classname="' + xmlEscape(group) + '" name="' + xmlEscape(r.name) + '">');
    if (!r.ok) {
        lines.push('    <failure message="' + xmlEscape((r.message || "").split("\n")[0]) + '">' +
            xmlEscape(r.message || "") + '</failure>');
    }
    lines.push('  </testcase>');
    console.log((r.ok ? "ok " : "not ok ") + r.name);
    if (!r.ok) {
        console.log("  " + (r.message || "").split("\n").join("\n  "));
    }
});
lines.push('</testsuite>');
fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, lines.join("\n") + "\n");
console.log("# " + group + ": " + (results.length - failures) + "/" + results.length + " passed");
