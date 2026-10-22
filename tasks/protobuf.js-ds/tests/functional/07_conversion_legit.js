"use strict";
// Ordinary plain-object conversion and serialization keep working, including
// fields whose names coincide with inherited properties when they are really
// present in the input.

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
    '  string ordinary = 5;' +
    '}' +
    'message PlainConverted { string ordinary = 1; }'
).root;
var Converted = root.lookupType("Converted");
var PlainConverted = root.lookupType("PlainConverted");

H.test("ordinary fields convert from and to plain objects", function () {
    var msg = Converted.fromObject({
        toString: "t",
        constructor: ["a", "b"],
        hasOwnProperty: { k: { x: "v" } },
        valueOf: { x: "n" },
        ordinary: "o"
    });
    H.strictEqual(msg.toString, "t");
    H.eq(msg.constructor, ["a", "b"]);
    H.strictEqual(msg.hasOwnProperty.k.x, "v");
    H.strictEqual(msg.valueOf.x, "n");
    H.strictEqual(msg.ordinary, "o");
    var round = Converted.toObject(msg);
    H.strictEqual(round.ordinary, "o");
    H.strictEqual(round.hasOwnProperty.k.x, "v");
});

H.test("messages without shadowing fields convert as before", function () {
    var msg = PlainConverted.fromObject({ ordinary: "o" });
    H.strictEqual(msg.ordinary, "o");
    H.eq(Object.keys(PlainConverted.toObject(msg)), ["ordinary"]);
});
