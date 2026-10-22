"use strict";
// Converting a plain object into a message looks fields up by name. A field
// that is absent from the input must not be read from the input's prototype.

var H = require("../support/harness");
var protobuf = H.product("");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'message Inner { string x = 1; }' +
    'message Converted {' +
    '  string toString = 1;' +
    '  repeated string constructor = 2;' +
    '  map<string, Inner> hasOwnProperty = 3;' +
    '  Inner valueOf = 4;' +
    '  string propertyIsEnumerable = 5;' +
    '  string isPrototypeOf = 6;' +
    '}'
).root;
var Converted = root.lookupType("Converted");

H.test("converting a plain object does not materialise absent fields from its prototype", function () {
    var msg = Converted.fromObject({});
    H.strictEqual(H.hasOwn(msg, "toString"), false, "absent field became own data");
    H.strictEqual(H.hasOwn(msg, "valueOf"), false, "absent field became own data");
    H.eq(msg.constructor, [], "absent repeated field is not empty");
    H.eq(msg.hasOwnProperty, {}, "absent map field is not empty");
    H.strictEqual(Converted.encode(msg).finish().length, 0, "absent fields were encoded");
});

H.test("converting a plain object does not read another inherited name from its prototype", function () {
    var msg = Converted.fromObject({});
    H.strictEqual(H.hasOwn(msg, "propertyIsEnumerable"), false,
        "absent field became own data");
    H.strictEqual(H.hasOwn(msg, "isPrototypeOf"), false,
        "absent field became own data");
    H.strictEqual(Converted.encode(msg).finish().length, 0, "absent fields were encoded");
});
