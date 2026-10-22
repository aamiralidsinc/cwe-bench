"use strict";
// Compiling a schema keeps the members of an aggregate option. A member name
// that coincides with a property every object inherits must be kept as the
// value written in the schema, not combined with anything inherited.

var H = require("../support/harness");
var protobuf = H.product("");

var source =
    'syntax = "proto2";\n' +
    'import "google/protobuf/descriptor.proto";\n' +
    'message Opt { optional string constructor = 1; optional string to_string = 2; optional string ordinary = 3; }\n' +
    'extend google.protobuf.MessageOptions { optional Opt opt = 50000; }\n' +
    'message Target { option (opt) = { constructor: "ctor" to_string: "str" ordinary: "plain" }; }\n';

H.test("a schema aggregate option keeps a shadowing member as plain data", function () {
    var root = protobuf.parse(source).root;
    var Target = root.lookupType("Target");
    var option = Target.parsedOptions[0]["(opt)"];
    H.strictEqual(option.constructor, "ctor", "shadowing member was not kept as data");
    H.strictEqual(option.to_string, "str", "ordinary member was not kept as data");
    H.strictEqual(option.ordinary, "plain", "ordinary member was not kept as data");
});
