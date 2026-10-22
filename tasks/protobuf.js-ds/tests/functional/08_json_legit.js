"use strict";
// Ordinary ProtoJSON parsing keeps working: maps, enums, duplicate-key
// rejection and round-trips.

var H = require("../support/harness");
var protobuf = H.product("");
var protojson = H.product("ext/protojson");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'enum Kind { ZERO = 0; ONE = 1; }' +
    'message Child { string name = 1; }' +
    'message JsonHolder { Kind kind = 1; map<string, Child> labels = 2; repeated string items = 3; }'
).root;
var JsonHolder = root.lookupType("JsonHolder");

H.test("ordinary JSON messages parse and round-trip", function () {
    var msg = protojson.fromJson(JsonHolder, {
        kind: "ONE",
        labels: { a: { name: "x" }, b: { name: "y" } },
        items: ["p", "q"]
    });
    H.strictEqual(msg.kind, 1);
    H.strictEqual(msg.labels.a.name, "x");
    H.eq(msg.items, ["p", "q"]);
    var json = protojson.toJson(JsonHolder, msg);
    H.strictEqual(json.kind, "ONE");
    H.strictEqual(json.labels.b.name, "y");
});

H.test("ordinary JSON map keys keep working and duplicates are rejected", function () {
    var msg = protojson.fromJson(JsonHolder, { labels: { plain: { name: "x" } } });
    H.eq(Object.keys(msg.labels), ["plain"]);
    H.throws(function () {
        protojson.fromJsonString(JsonHolder, '{"labels":{"a":{"name":"x"},"a":{"name":"y"}}}');
    }, "duplicate JSON map key was accepted");
});
