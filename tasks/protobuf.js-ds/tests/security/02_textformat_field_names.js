"use strict";
// A field name in the input that coincides with a property every object
// inherits must be handled as an ordinary field: parsed as data, not read
// from, or written to, the object prototype.

var H = require("../support/harness");
var protobuf = H.product("");
var textformat = H.product("ext/textformat");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'message ShadowFields {' +
    '  repeated string toString = 1;' +
    '  map<string, string> hasOwnProperty = 2;' +
    '  repeated string propertyIsEnumerable = 3;' +
    '  map<string, string> isPrototypeOf = 4;' +
    '}'
).root;
var ShadowFields = root.lookupType("ShadowFields");

H.test("a repeated field whose name shadows an inherited property parses as data", function () {
    var msg = textformat.fromText(ShadowFields, 'toString: "x" toString: "y"');
    H.ok(H.hasOwn(msg, "toString"), "field is not an own property");
    H.eq(msg.toString, ["x", "y"], "repeated field was not parsed as data");
});

H.test("the list form of a repeated field with a shadowing name parses as data", function () {
    var msg = textformat.fromText(ShadowFields, 'toString: ["x", "y"]');
    H.ok(H.hasOwn(msg, "toString"), "field is not an own property");
    H.eq(msg.toString, ["x", "y"], "repeated list field was not parsed as data");
});

H.test("a map field whose name shadows an inherited property parses as data without side effects", function () {
    try {
        var msg = textformat.fromText(ShadowFields, 'hasOwnProperty { key: "a" value: "b" }');
        H.ok(H.hasOwn(msg, "hasOwnProperty"), "field is not an own property");
        H.eq(msg.hasOwnProperty, { a: "b" }, "map field was not parsed as data");
        H.strictEqual(H.hasOwn(Object.prototype.hasOwnProperty, "a"), false,
            "parsing modified the shared inherited function");
    } finally {
        delete Object.prototype.hasOwnProperty.a;
    }
});

H.test("a repeated field named like a different inherited property parses as data", function () {
    var msg = textformat.fromText(ShadowFields, 'propertyIsEnumerable: "z"');
    H.ok(H.hasOwn(msg, "propertyIsEnumerable"), "field is not an own property");
    H.eq(msg.propertyIsEnumerable, ["z"], "repeated field was not parsed as data");
});

H.test("a map field named like a different inherited property parses without side effects", function () {
    try {
        var msg = textformat.fromText(ShadowFields, 'isPrototypeOf { key: "a" value: "b" }');
        H.ok(H.hasOwn(msg, "isPrototypeOf"), "field is not an own property");
        H.eq(msg.isPrototypeOf, { a: "b" }, "map field was not parsed as data");
        H.strictEqual(H.hasOwn(Object.prototype.isPrototypeOf, "a"), false,
            "parsing modified the shared inherited function");
    } finally {
        delete Object.prototype.isPrototypeOf.a;
    }
});
