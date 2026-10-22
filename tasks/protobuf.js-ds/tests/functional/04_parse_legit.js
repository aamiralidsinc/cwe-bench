"use strict";
// Ordinary schema compilation keeps working: options, aggregate options,
// repeated option members and message/field references.

var H = require("../support/harness");
var protobuf = H.product("");

var source =
    'syntax = "proto2";\n' +
    'import "google/protobuf/descriptor.proto";\n' +
    'message Opt { optional string a = 1; optional string b = 2; repeated string list = 3; }\n' +
    'extend google.protobuf.MessageOptions { optional Opt opt = 50000; }\n' +
    'message Target {\n' +
    '  option (opt) = { a: "one" b: "two" list: ["x", "y"] };\n' +
    '  optional string field = 1 [deprecated = true];\n' +
    '}\n';

H.test("ordinary aggregate option members and repeated members are kept", function () {
    var root = protobuf.parse(source).root;
    var Target = root.lookupType("Target");
    var option = Target.parsedOptions[0]["(opt)"];
    H.strictEqual(option.a, "one");
    H.strictEqual(option.b, "two");
    H.eq(option.list, ["x", "y"]);
    H.strictEqual(Target.fields.field.getOption("deprecated"), true, "ordinary field option lost");
});

H.test("ordinary dotted parsed options are nested and merged", function () {
    var root = protobuf.parse(
        'syntax = "proto2";\n' +
        'import "google/protobuf/descriptor.proto";\n' +
        'message Named { optional string a = 1; optional string b = 2; }\n' +
        'extend google.protobuf.MessageOptions { optional Named named = 50010; }\n' +
        'message Target2 { option (named).a = "x"; option (named).b = "y"; }\n'
    ).root;
    var option = root.lookupType("Target2").parsedOptions[0]["(named)"];
    H.strictEqual(option.a, "x");
    H.strictEqual(option.b, "y");
});
