"use strict";
// A map key taken from text-format input must be stored as an ordinary own
// data key: it must not reach the returned map's prototype, and the map must
// keep the prototype an ordinary object has.

var H = require("../support/harness");
var protobuf = H.product("");
var textformat = H.product("ext/textformat");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'message Value { bool admin = 1; string role = 2; }' +
    'message MapHolder {' +
    '  map<string, Value> labels = 1;' +
    '  map<string, string> tags = 2;' +
    '}'
).root;
var MapHolder = root.lookupType("MapHolder");

function assertSafeMap(map, key, message) {
    H.strictEqual(Object.getPrototypeOf(map), Object.prototype, message + ": prototype changed");
    H.ok(H.hasOwn(map, key), message + ": key is not an own property");
    H.ok(Object.keys(map).indexOf(key) >= 0, message + ": key is not enumerable");
}

H.test("a text-format map entry with a brace-delimited __proto__ key stays data", function () {
    var msg = textformat.fromText(MapHolder,
        'labels { key: "__proto__" value { admin: true role: "owner" } }');
    assertSafeMap(msg.labels, "__proto__", "brace form");
    H.strictEqual(msg.labels["__proto__"].admin, true, "map value lost");
    H.strictEqual(msg.labels["__proto__"].role, "owner", "map value incomplete");
    H.strictEqual("admin" in msg.labels, false, "value fields leaked through the map prototype");
    H.strictEqual("role" in msg.labels, false, "value fields leaked through the map prototype");
});

H.test("a text-format map entry with an angle-delimited __proto__ key stays data", function () {
    var msg = textformat.fromText(MapHolder,
        'labels < key: "__proto__" value < admin: true role: "owner" > >');
    assertSafeMap(msg.labels, "__proto__", "angle form");
    H.strictEqual(msg.labels["__proto__"].admin, true, "map value lost");
    H.strictEqual("admin" in msg.labels, false, "value fields leaked through the map prototype");
});

H.test("a text-format map list keeps a __proto__ entry as data next to ordinary entries", function () {
    var msg = textformat.fromText(MapHolder,
        'labels: [ { key: "__proto__" value { admin: true } }, { key: "ok" value { admin: false } } ]');
    assertSafeMap(msg.labels, "__proto__", "list form");
    assertSafeMap(msg.labels, "ok", "list form");
    H.strictEqual(msg.labels["__proto__"].admin, true, "map value lost");
    H.strictEqual(msg.labels.ok.admin, false, "ordinary entry lost");
    H.strictEqual("admin" in msg.labels, false, "value fields leaked through the map prototype");
});

H.test("a scalar map entry with a __proto__ key stays data", function () {
    var msg = textformat.fromText(MapHolder, 'tags { key: "__proto__" value: "x" }');
    assertSafeMap(msg.tags, "__proto__", "scalar map");
    H.strictEqual(msg.tags["__proto__"], "x", "scalar map value lost");
});
