"use strict";
// Dotted parsed options carry a name path taken from the schema. A path
// segment that coincides with an inherited property must be kept as the value
// written in the schema, and an unsafe segment must not change the container.

var H = require("../support/harness");
var protobuf = H.product("");

var header =
    'syntax = "proto2";\n' +
    'import "google/protobuf/descriptor.proto";\n' +
    'message NamedOpt { optional string a = 1; optional string toString = 2; }\n' +
    'extend google.protobuf.MessageOptions { optional NamedOpt named = 50010; }\n';

H.test("a dotted parsed option keeps a shadowing segment as the given value", function () {
    var root = protobuf.parse(header +
        'message ParsedTarget { option (named).a = "x"; option (named).toString = "v"; }'
    ).root;
    var option = root.lookupType("ParsedTarget").parsedOptions[0]["(named)"];
    H.strictEqual(option.a, "x", "ordinary segment was not kept");
    H.strictEqual(option.toString, "v", "shadowing segment was not kept as data");
});

H.test("a dotted parsed option with an unsafe segment leaves the option object prototype alone", function () {
    var root = protobuf.parse(header +
        'message ParsedUnsafe { option (named).a = "x"; option (named).__proto__ = { marker: true }; }'
    ).root;
    var option = root.lookupType("ParsedUnsafe").parsedOptions[0]["(named)"];
    H.strictEqual(Object.getPrototypeOf(option), Object.prototype,
        "parsed option object prototype changed");
    H.strictEqual(option.marker, undefined, "value leaked through the prototype");
    H.strictEqual(option.a, "x", "ordinary segment was not kept");
});
