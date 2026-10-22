"use strict";
// The bundled code generator keeps producing working modules for ordinary
// schemas: enums, messages, maps and conversions.

var H = require("../support/harness");
var child = require("child_process");
var fs = require("fs");
var os = require("os");
var path = require("path");

var dir = fs.mkdtempSync(path.join(os.tmpdir(), "pbjs-functional-"));
var protoFile = path.join(dir, "plain.proto");
var outFile = path.join(dir, "plain.js");
fs.writeFileSync(protoFile,
    'syntax = "proto3";\n' +
    'package p;\n' +
    'enum E { A = 0; B = 1; }\n' +
    'message Child { string name = 1; }\n' +
    'message M { E e = 1; map<string, Child> labels = 2; }\n');

var mod = null;
function load() {
    if (mod)
        return mod;
    var res = child.spawnSync(process.execPath, [
        path.join(H.APP, "cli", "bin", "pbjs"),
        "-t", "static-module",
        "--dependency", H.APP,
        "-o", outFile,
        protoFile
    ], { encoding: "utf8" });
    H.strictEqual(res.status, 0, "code generation failed: " + String(res.stderr || "").slice(0, 400));
    mod = require(outFile);
    return mod;
}

H.test("a generated module encodes and decodes ordinary messages", function () {
    var m = load();
    var msg = m.p.M.create({ e: 1, labels: { a: { name: "x" } } });
    var decoded = m.p.M.decode(m.p.M.encode(msg).finish());
    H.strictEqual(decoded.e, 1);
    H.strictEqual(decoded.labels.a.name, "x");
    H.strictEqual(m.p.E.A, 0);
    H.strictEqual(m.p.E.B, 1);
});

H.test("a generated module converts ordinary plain objects", function () {
    var m = load();
    var msg = m.p.M.fromObject({ e: "B", labels: { a: { name: "y" } } });
    H.strictEqual(msg.e, 1);
    H.strictEqual(msg.labels.a.name, "y");
    var obj = m.p.M.toObject(msg);
    H.strictEqual(obj.labels.a.name, "y");
});

H.test("generated schema text keeps ordinary extension declarations", function () {
    var outDir = fs.mkdtempSync(path.join(os.tmpdir(), "pbjs-functional-proto-"));
    var sourceFile = path.join(outDir, "plain.proto");
    var outFile = path.join(outDir, "plain.out.proto");
    fs.writeFileSync(sourceFile,
        'syntax = "proto2";\n' +
        'package p;\n' +
        'message Outer {\n' +
        '  message Target { extensions 100 to 200; }\n' +
        '  extend Target { optional string extra = 100; }\n' +
        '  optional Target target = 1;\n' +
        '}\n');
    var res = child.spawnSync(process.execPath, [
        path.join(H.APP, "cli", "bin", "pbjs"),
        "-t", "proto",
        "-o", outFile,
        sourceFile
    ], { encoding: "utf8" });
    H.strictEqual(res.status, 0, "schema generation failed: " + String(res.stderr || "").slice(0, 400));
    var text = fs.readFileSync(outFile, "utf8");
    H.ok(text.indexOf("extend Target") >= 0, "the extension declaration was lost");
    H.ok(text.indexOf("extra") >= 0, "the extension field was lost");
    H.ok(text.indexOf("target") >= 0, "the ordinary field was lost");
});
