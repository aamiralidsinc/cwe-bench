"use strict";
// Ordinary text-format parsing must keep working exactly as before, and the
// map container must keep the ordinary object prototype callers rely on.

var H = require("../support/harness");
var protobuf = H.product("");
var textformat = H.product("ext/textformat");

var root = protobuf.parse(
    'syntax = "proto3";' +
    'message Child { string name = 1; }' +
    'message Plain {' +
    '  int32 count = 1;' +
    '  string title = 2;' +
    '  repeated int32 numbers = 3;' +
    '  repeated Child children = 4;' +
    '  map<string, Child> labels = 5;' +
    '  map<string, string> tags = 6;' +
    '}'
).root;
var Plain = root.lookupType("Plain");

H.test("scalar, repeated, nested and map text-format fields parse as before", function () {
    var msg = textformat.fromText(Plain,
        'count: 7 title: "hello" numbers: [1, 2, 3] ' +
        'children { name: "a" } children { name: "b" } ' +
        'labels { key: "k" value { name: "v" } } tags { key: "t" value: "u" }');
    H.strictEqual(msg.count, 7);
    H.strictEqual(msg.title, "hello");
    H.eq(msg.numbers, [1, 2, 3]);
    H.strictEqual(msg.children.length, 2);
    H.strictEqual(msg.labels.k.name, "v");
    H.strictEqual(msg.tags.t, "u");
});

H.test("a map keeps the ordinary object prototype for ordinary keys", function () {
    var msg = textformat.fromText(Plain, 'labels { key: "a" value { name: "x" } }');
    H.strictEqual(Object.getPrototypeOf(msg.labels), Object.prototype,
        "ordinary map changed its prototype");
    H.eq(Object.keys(msg.labels), ["a"]);
});

H.test("empty lists and map entries with a missing key keep their defaults", function () {
    var msg = textformat.fromText(Plain, 'numbers: [] labels: [] labels { value { name: "defaulted" } }');
    H.eq(msg.numbers, []);
    H.eq(Object.keys(msg.labels), [""]);
    H.strictEqual(msg.labels[""].name, "defaulted");
});

H.test("a later map entry with the same key overwrites the earlier value", function () {
    var msg = textformat.fromText(Plain,
        'labels { key: "a" value { name: "first" } } labels { key: "a" value { name: "second" } }');
    H.eq(Object.keys(msg.labels), ["a"]);
    H.strictEqual(msg.labels.a.name, "second");
});

H.test("ordinary messages format back to text", function () {
    var msg = textformat.fromText(Plain, 'count: 1 labels { key: "a" value { name: "x" } }');
    var text = textformat.toText(Plain, msg);
    H.ok(text.indexOf("count: 1") >= 0, "count missing from formatted text");
    H.ok(text.indexOf('key: "a"') >= 0, "map key missing from formatted text");
});
