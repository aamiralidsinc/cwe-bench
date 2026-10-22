"use strict";
// Ordinary option handling and merging keeps working, including the existing
// refusal of unsafe option names.

var H = require("../support/harness");
var protobuf = H.product("");

H.test("ordinary options can be set, read and merged", function () {
    var type = new protobuf.Type("OptionHolder");
    H.strictEqual(type.getOption("ordinary"), undefined, "unset option should be absent");
    type.setOption("ordinary", 1);
    H.strictEqual(type.getOption("ordinary"), 1);
    type.setOption("ordinary", 2, true);
    H.strictEqual(type.getOption("ordinary"), 1, "ifNotSet overwrote an existing option");
    type.setOptions({ first: "a", second: "b" });
    H.strictEqual(type.getOption("first"), "a");
    H.strictEqual(type.getOption("second"), "b");
});

H.test("an unsafe option name is ignored and leaves the options object shape alone", function () {
    var type = new protobuf.Type("UnsafeOptionHolder");
    type.setOption("ordinary", 1);
    type.setOption("__proto__", { marker: true });
    H.strictEqual(Object.getPrototypeOf(type.options), Object.prototype, "options prototype changed");
    H.strictEqual(H.hasOwn(type.options, "__proto__"), false, "unsafe option was stored");
    H.strictEqual(type.getOption("ordinary"), 1);
});

H.test("ordinary merging keeps its documented semantics", function () {
    var dst = protobuf.util.merge({}, { a: 1, b: 2 });
    H.eq(dst, { a: 1, b: 2 });
    protobuf.util.merge(dst, { a: 9, c: 3 }, true);
    H.eq(dst, { a: 1, b: 2, c: 3 });
    var guarded = {};
    protobuf.util.merge(guarded, JSON.parse('{"__proto__":{"marker":true},"prototype":1,"constructor":2,"safe":3}'));
    H.strictEqual(Object.getPrototypeOf(guarded), Object.prototype, "merge changed the prototype");
    H.strictEqual(H.hasOwn(guarded, "__proto__"), false);
    H.strictEqual(H.hasOwn(guarded, "prototype"), false);
    H.strictEqual(H.hasOwn(guarded, "constructor"), false);
    H.strictEqual(guarded.safe, 3);
});
