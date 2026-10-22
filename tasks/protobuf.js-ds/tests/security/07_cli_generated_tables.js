"use strict";
// The bundled code generator emits name-keyed tables. Tables it emits for
// name-based lookup must not resolve an undeclared name to an inherited
// property, and the conversion code it emits must not read absent fields from
// the input object's prototype.

var H = require("../support/harness");
var child = require("child_process");
var fs = require("fs");
var os = require("os");
var path = require("path");

var dir = fs.mkdtempSync(path.join(os.tmpdir(), "pbjs-generator-"));
var protoFile = path.join(dir, "table.proto");
var outFile = path.join(dir, "table.js");
fs.writeFileSync(protoFile,
    'syntax = "proto3";\n' +
    'package p;\n' +
    'enum E { A = 0; B = 1; }\n' +
    'message M { E e = 1; string toString = 2; }\n');

var generated = null;
function loadGenerated() {
    if (generated)
        return generated;
    var res = child.spawnSync(process.execPath, [
        path.join(H.APP, "cli", "bin", "pbjs"),
        "-t", "static-module",
        "--dependency", H.APP,
        "-o", outFile,
        protoFile
    ], { encoding: "utf8" });
    H.strictEqual(res.status, 0, "code generation failed: " + String(res.stderr || "").slice(0, 400));
    generated = require(outFile);
    return generated;
}

H.test("an emitted enum table does not resolve inherited properties as values", function () {
    var mod = loadGenerated();
    var E = mod.p.E;
    H.strictEqual(E.A, 0, "declared value lost");
    H.strictEqual(E.B, 1, "declared value lost");
    H.strictEqual(E.toString, undefined, "inherited function exposed as an enum value");
    H.strictEqual(E.constructor, undefined, "inherited constructor exposed as an enum value");
    H.strictEqual(E.isPrototypeOf, undefined, "inherited function exposed as an enum value");
    H.strictEqual(E.propertyIsEnumerable, undefined, "inherited function exposed as an enum value");
});

H.test("emitted conversion code does not read an absent field from the input prototype", function () {
    var mod = loadGenerated();
    var msg = mod.p.M.fromObject({});
    H.strictEqual(H.hasOwn(msg, "toString"), false, "absent field was materialised as data");
    H.strictEqual(mod.p.M.encode(msg).finish().length, 0, "absent field was encoded");
});

H.test("generated schema text does not resolve an extension target against an inherited property", function () {
    var outDir = fs.mkdtempSync(path.join(os.tmpdir(), "pbjs-proto-"));
    var extensionFile = path.join(outDir, "extension.proto");
    var schemaOut = path.join(outDir, "extension.out.proto");
    fs.writeFileSync(extensionFile,
        'syntax = "proto2";\n' +
        'package p;\n' +
        'message Outer {\n' +
        '  message toString { extensions 100 to 200; }\n' +
        '  extend toString { optional string extra = 100; }\n' +
        '}\n');
    var res = child.spawnSync(process.execPath, [
        path.join(H.APP, "cli", "bin", "pbjs"),
        "-t", "proto",
        "-o", schemaOut,
        extensionFile
    ], { encoding: "utf8" });
    H.strictEqual(res.status, 0,
        "schema generation failed: " + String(res.stderr || "").slice(0, 400));
    var text = fs.readFileSync(schemaOut, "utf8");
    H.ok(text.indexOf("extend toString") >= 0, "the extension declaration was lost");
    H.ok(text.indexOf("extra") >= 0, "the extension field was lost");
});
