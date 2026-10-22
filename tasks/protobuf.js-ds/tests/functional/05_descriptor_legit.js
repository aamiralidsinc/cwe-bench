"use strict";
// Ordinary descriptor import keeps working: messages, map fields and enums,
// including an enum value whose name coincides with an inherited property.

var H = require("../support/harness");
var protobuf = H.product("");
var descriptor = H.product("ext/descriptor");

H.test("a normal descriptor builds messages with map fields and enums", function () {
    var fileDescriptor = descriptor.FileDescriptorProto.create({
        name: "normal.proto",
        package: "p",
        messageType: [{
            name: "M",
            field: [{
                name: "tags",
                number: 1,
                label: 3,
                type: 11,
                typeName: ".p.M.TagsEntry"
            }],
            nestedType: [{
                name: "TagsEntry",
                options: { mapEntry: true },
                field: [
                    { name: "key", number: 1, label: 1, type: 9 },
                    { name: "value", number: 2, label: 1, type: 9 }
                ]
            }]
        }],
        enumType: [{
            name: "E",
            value: [
                { name: "A", number: 0 },
                { name: "constructor", number: 1 }
            ]
        }]
    });
    var root = protobuf.Root.fromDescriptor(
        descriptor.FileDescriptorSet.create({ file: [fileDescriptor] }));
    var M = root.lookupType("p.M");
    H.strictEqual(M.fields.tags.map, true, "map field not recognised");
    var msg = M.fromObject({ tags: { a: "b" } });
    H.strictEqual(msg.tags.a, "b", "map value lost");
    var E = root.lookupEnum("p.E");
    H.strictEqual(E.values.A, 0);
    H.strictEqual(E.values.constructor, 1, "shadowing enum value lost");
    H.strictEqual(E.valuesById[1], "constructor", "shadowing enum value lost by id");
});
