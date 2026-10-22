"use strict";
// Minimal in-process test registry for the hidden suites. Tests register
// themselves at require time; run_group.js executes them and writes JUnit XML.
// Expected values and clean-ups are plain JavaScript on purpose: a hardened
// product helper must not be needed to decide whether a test passed.

var assert = require("assert");
var path = require("path");

var APP = process.env.APP_DIR || "/app";

var tests = [];

function test(name, fn) {
    tests.push({ name: name, fn: fn });
}

function list() {
    return tests;
}

function ok(value, message) {
    assert.ok(value, message);
}

function eq(actual, expected, message) {
    assert.deepStrictEqual(actual, expected, message);
}

function strictEqual(actual, expected, message) {
    assert.strictEqual(actual, expected, message);
}

function throws(fn, message) {
    var threw = false;
    try {
        fn();
    } catch (e) {
        threw = true;
    }
    assert.ok(threw, message || "expected an error");
}

function hasOwn(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
}

function product(rel) {
    return require(path.join(APP, rel));
}

module.exports = {
    APP: APP,
    test: test,
    list: list,
    ok: ok,
    eq: eq,
    strictEqual: strictEqual,
    throws: throws,
    hasOwn: hasOwn,
    product: product
};
