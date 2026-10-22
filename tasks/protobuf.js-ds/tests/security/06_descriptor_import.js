"use strict";
// Importing a descriptor set turns names from the descriptor into table
// entries. An unsafe value name must not change a table's prototype or make
// the value's settings readable through inheritance, while ordinary values
// are preserved.

var H = require("../support/harness");
var protobuf = H.product("");
var descriptor = H.product("ext/descriptor");

function fileSet(messageType) {
    return descriptor.FileDescriptorSet.create({
        file: [descriptor.FileDescriptorProto.create({
            name: "shadow.proto",
            package: "p",
            messageType: messageType
        })]
    });
}

H.test("an imported enum value named __proto__ cannot leak its options through the prototype", function () {
    var enumDescriptor = descriptor.EnumDescriptorProto.create({
        name: "Unsafe",
        value: [
            { name: "__proto__", number: 0, options: { deprecated: true } },
            { name: "OK", number: 1, options: { deprecated: false } }
        ]
    });
    var enm = protobuf.Enum.fromDescriptor(enumDescriptor);
    H.strictEqual(Object.getPrototypeOf(enm.valuesOptions), Object.prototype,
        "values-options table prototype changed");
    H.strictEqual(enm.valuesOptions.deprecated, undefined,
        "settings of the unsafe value leaked through inheritance");
    H.strictEqual(enm.values.OK, 1, "ordinary value lost");
    H.strictEqual(enm.valuesById[1], "OK", "ordinary value lost by id");
    H.eq(enm.valuesOptions.OK, { deprecated: false }, "ordinary value settings lost");
});

H.test("an imported field whose type name matches an inherited property is not treated as a map entry", function () {
    var root = protobuf.Root.fromDescriptor(fileSet([{
        name: "Holder",
        field: [{
            name: "items",
            number: 1,
            label: 3,
            type: 11,
            typeName: ".p.Holder.toString"
        }],
        nestedType: [{
            name: "toString",
            field: [{ name: "x", number: 1, label: 1, type: 9 }]
        }]
    }]));
    var Holder = root.lookupType("p.Holder");
    H.strictEqual(Holder.fields.items.repeated, true, "the imported repeated field was lost");
    H.ok(!Holder.fields.items.map, "a non-map field was resolved to an inherited property");
    var msg = Holder.create({ items: [{ x: "a" }, { x: "b" }] });
    var decoded = Holder.decode(Holder.encode(msg).finish());
    H.eq(decoded.items.map(function (item) { return item.x; }), ["a", "b"],
        "ordinary values of the imported field did not round-trip");
});

H.test("an imported nested type is not marked as a group from an inherited property", function () {
    var root = protobuf.Root.fromDescriptor(fileSet([{
        name: "M",
        field: [{ name: "x", number: 1, label: 1, type: 9 }],
        nestedType: [{
            name: "toString",
            field: [{ name: "y", number: 1, label: 1, type: 9 }]
        }]
    }]));
    var nested = root.lookupType("p.M.toString");
    H.ok(!nested.group, "a nested type was marked as a group by an inherited property");
    H.strictEqual(nested.toJSON().group, undefined,
        "the imported shape was changed by an inherited property");
    var M = root.lookupType("p.M");
    var msg = M.create({ x: "v" });
    H.strictEqual(M.toObject(M.decode(M.encode(msg).finish())).x, "v",
        "the imported type no longer round-trips ordinary data");
});
