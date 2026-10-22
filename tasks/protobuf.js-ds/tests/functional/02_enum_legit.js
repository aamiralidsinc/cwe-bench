"use strict";
// Ordinary enum use: declarations, text and JSON parsing, numeric lookup and
// JSON round-trips keep working.

var H = require("../support/harness");
var protobuf = H.product("");
var textformat = H.product("ext/textformat");
var protojson = H.product("ext/protojson");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'enum Kind { ZERO = 0; ONE = 1; }' +
    'message Envelope { Kind kind = 1; repeated Kind kinds = 2; }'
).root;
var Envelope = root.lookupType("Envelope");
var Kind = root.lookupEnum("Kind");

H.test("ordinary enum values parse from text format and keep numeric lookup", function () {
    var msg = textformat.fromText(Envelope, "kind: ONE kinds: [ZERO, ONE]");
    H.strictEqual(msg.kind, 1);
    H.eq(msg.kinds, [0, 1]);
    H.strictEqual(Kind.values.ZERO, 0);
    H.strictEqual(Kind.valuesById[1], "ONE", "numeric lookup by id stopped working");
    H.strictEqual(Kind.values[1], "ONE", "numeric lookup through the values table stopped working");
});

H.test("ordinary enum values parse from JSON", function () {
    var msg = protojson.fromJson(Envelope, { kind: "ONE", kinds: ["ZERO", 1] });
    H.strictEqual(msg.kind, 1);
    H.eq(msg.kinds, [0, 1]);
});

H.test("enum JSON import and export keep working", function () {
    var enm = protobuf.Enum.fromJSON("Imported", { values: { A: 0, B: 1 } });
    H.strictEqual(enm.values.A, 0);
    H.strictEqual(enm.valuesById[1], "B");
    var json = enm.toJSON();
    H.strictEqual(json.values.A, 0, "exported enum value lost");
    H.strictEqual(json.values.B, 1, "exported enum value lost");
});

H.test("an enum value declared under a shadowing name through JSON import works", function () {
    var enm = protobuf.Enum.fromJSON("ImportedShadow", { values: { toString: 0 } });
    H.strictEqual(enm.values.toString, 0, "shadowing value was not imported");
});
