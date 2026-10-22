"use strict";
// Named settings and merged defaults must distinguish a value that was really
// recorded from a property the object merely inherits.

var H = require("../support/harness");
var protobuf = H.product("");

H.test("an unset option is not read from the object prototype", function () {
    var type = new protobuf.Type("OptionHolder");
    type.setOption("ordinary", 1);
    H.strictEqual(type.getOption("toString"), undefined, "inherited function returned as an option");
    H.strictEqual(type.getOption("constructor"), undefined, "inherited function returned as an option");
    H.strictEqual(type.getOption("isPrototypeOf"), undefined, "inherited function returned as an option");
    H.strictEqual(type.getOption("propertyIsEnumerable"), undefined, "inherited function returned as an option");
    H.strictEqual(type.getOption("ordinary"), 1, "an ordinary option stopped working");
});

H.test("an option whose name shadows an inherited property can be set and read", function () {
    var type = new protobuf.Type("ShadowOptionHolder");
    type.setOption("toString", "custom", true);
    H.strictEqual(type.getOption("toString"), "custom", "shadowing option was not stored");
    type.setOption("toString", "ignored", true);
    H.strictEqual(type.getOption("toString"), "custom", "ifNotSet overwrote an existing option");
    type.setOption("constructor", "ctor", true);
    H.strictEqual(type.getOption("constructor"), "ctor", "shadowing option was not stored");
});

H.test("merging defaults does not treat an inherited property as already set", function () {
    var dst = {};
    protobuf.util.merge(dst, { toString: "value" }, true);
    H.ok(H.hasOwn(dst, "toString"), "merged key is not an own property");
    H.strictEqual(dst.toString, "value", "merged value was dropped");
    var other = {};
    protobuf.util.merge(other, { isPrototypeOf: "value", propertyIsEnumerable: "value2" }, true);
    H.ok(H.hasOwn(other, "isPrototypeOf"), "merged key is not an own property");
    H.ok(H.hasOwn(other, "propertyIsEnumerable"), "merged key is not an own property");
    H.strictEqual(other.isPrototypeOf, "value", "merged value was dropped");
    H.strictEqual(other.propertyIsEnumerable, "value2", "merged value was dropped");
});
