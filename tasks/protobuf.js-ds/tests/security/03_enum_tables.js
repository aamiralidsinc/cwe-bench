"use strict";
// Enum values are looked up by a name taken from the input. A name that was
// never declared must be reported as invalid, never resolved to a property
// the values table inherits; a declared name that happens to coincide with
// such a property must remain usable.

var H = require("../support/harness");
var protobuf = H.product("");
var textformat = H.product("ext/textformat");
var protojson = H.product("ext/protojson");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'enum Kind { ZERO = 0; ONE = 1; }' +
    'message Envelope { Kind kind = 1; }'
).root;
var Envelope = root.lookupType("Envelope");

H.test("a text-format enum name inherited from the object prototype is rejected", function () {
    H.throws(function () {
        textformat.fromText(Envelope, "kind: constructor");
    }, "inherited name was accepted as an enum value");
    H.throws(function () {
        textformat.fromText(Envelope, "kind: toString");
    }, "inherited name was accepted as an enum value");
    H.throws(function () {
        textformat.fromText(Envelope, "kind: isPrototypeOf");
    }, "inherited name was accepted as an enum value");
    H.throws(function () {
        textformat.fromText(Envelope, "kind: propertyIsEnumerable");
    }, "inherited name was accepted as an enum value");
});

H.test("a JSON enum name inherited from the object prototype is rejected", function () {
    H.throws(function () {
        protojson.fromJson(Envelope, { kind: "constructor" });
    }, "inherited name was accepted as an enum value");
    H.throws(function () {
        protojson.fromJson(Envelope, { kind: "toString" });
    }, "inherited name was accepted as an enum value");
    H.throws(function () {
        protojson.fromJson(Envelope, { kind: "isPrototypeOf" });
    }, "inherited name was accepted as an enum value");
    H.throws(function () {
        protojson.fromJson(Envelope, { kind: "propertyIsEnumerable" });
    }, "inherited name was accepted as an enum value");
});

H.test("an enum values table does not expose inherited properties as values", function () {
    var enm = new protobuf.Enum("Shadow", {});
    H.strictEqual(enm.values.constructor, undefined, "constructor leaked from the table");
    H.strictEqual(enm.values.toString, undefined, "toString leaked from the table");
    H.strictEqual(enm.values.isPrototypeOf, undefined, "isPrototypeOf leaked from the table");
    H.strictEqual(enm.values.propertyIsEnumerable, undefined, "propertyIsEnumerable leaked from the table");
});

H.test("a schema may declare enum values whose names shadow inherited properties", function () {
    var parsed = protobuf.parse(
        'syntax = "proto3";' +
        'enum Shady { constructor = 0; toString = 1; }' +
        'message ShadyHolder { Shady value = 1; }'
    ).root;
    var enm = parsed.lookupEnum("Shady");
    H.strictEqual(enm.values.constructor, 0, "declared shadowing value missing");
    H.strictEqual(enm.values.toString, 1, "declared shadowing value missing");
    H.strictEqual(enm.valuesById[1], "toString", "declared shadowing value missing by id");
    var holder = parsed.lookupType("ShadyHolder");
    var msg = textformat.fromText(holder, "value: constructor");
    H.strictEqual(msg.value, 0, "declared shadowing value did not parse");
});

H.test("an enum value with a shadowing name can be added through the public API", function () {
    var enm = new protobuf.Enum("Added", {});
    enm.add("constructor", 2);
    H.strictEqual(enm.values.constructor, 2, "shadowing name not stored as data");
    H.strictEqual(enm.valuesById[2], "constructor", "shadowing name not stored by id");
});

H.test("a refused enum lookup leaves the table intact and parsing working", function () {
    var Kind = Envelope.fields.kind.resolvedType;
    var before = Object.keys(Kind.values).sort();
    H.throws(function () {
        textformat.fromText(Envelope, "kind: propertyIsEnumerable");
    }, "inherited name was accepted as an enum value");
    H.eq(Object.keys(Kind.values).sort(), before, "a refused lookup changed the enum table");
    H.strictEqual(Kind.valuesById[1], "ONE", "a refused lookup changed numeric lookup");
    H.strictEqual(Kind.values.ZERO, 0, "a refused lookup lost a declared value");
    H.strictEqual(textformat.fromText(Envelope, "kind: ONE").kind, 1,
        "a valid message no longer parses after a refusal");
});
