"use strict";
// Settings written by a dotted path: every segment is a name, and no segment
// may be resolved to a property the containing object inherits. A segment
// that cannot be a safe property must leave the container's prototype alone.

var H = require("../support/harness");
var protobuf = H.product("");

H.test("a dotted setting keeps the given value instead of an inherited property", function () {
    var type = new protobuf.Type("DottedHolder");
    type.setOption("features.toString", "EXPLICIT");
    H.strictEqual(type.options.features.toString, "EXPLICIT", "inherited property mixed into the value");
});

H.test("a dotted setting with an inherited inner segment does not modify the shared prototype", function () {
    try {
        var type = new protobuf.Type("DottedInner");
        type.setOption("features.toString.inner", "v");
        H.strictEqual(Object.prototype.toString.inner, undefined,
            "a shared inherited function was modified");
        H.strictEqual(type.options.features.toString.inner, "v", "setting was not stored");
    } finally {
        delete Object.prototype.toString.inner;
    }
});

H.test("a schema keeps a dotted feature setting as plain data", function () {
    var root = protobuf.parse(
        'syntax = "proto3";' +
        'message DottedSchema { option features.toString = "EXPLICIT"; string a = 1; }'
    ).root;
    var DottedSchema = root.lookupType("DottedSchema");
    H.strictEqual(DottedSchema.options.features.toString, "EXPLICIT", "setting was not kept as data");
});

H.test("a dotted setting with an unsafe final name leaves the container prototype alone", function () {
    var type = new protobuf.Type("UnsafeSegment");
    type.setOption("features.__proto__", { marker: true });
    H.strictEqual(Object.getPrototypeOf(type.options.features), Object.prototype,
        "container prototype changed");
    H.strictEqual(type.options.features.marker, undefined, "value leaked through the prototype");
});

H.test("a schema with an unsafe dotted setting leaves the container prototype alone", function () {
    var root = protobuf.parse(
        'syntax = "proto3";' +
        'message UnsafeSchema { option features.__proto__ = { marker: true }; string a = 1; }'
    ).root;
    var UnsafeSchema = root.lookupType("UnsafeSchema");
    H.ok(UnsafeSchema.options && UnsafeSchema.options.features, "feature settings were not recorded");
    H.strictEqual(Object.getPrototypeOf(UnsafeSchema.options.features), Object.prototype,
        "container prototype changed");
    H.strictEqual(UnsafeSchema.options.features.marker, undefined, "value leaked through the prototype");
    var parsed = UnsafeSchema.parsedOptions[0]["features"];
    H.ok(parsed, "the parsed option was not recorded");
    H.strictEqual(Object.getPrototypeOf(parsed), Object.prototype,
        "parsed option container prototype changed");
    H.strictEqual(parsed.marker, undefined, "value leaked through the parsed option prototype");
});
