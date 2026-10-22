"use strict";
// The project's own tests for the affected area, run from a pristine copy kept
// outside the working tree, must still pass.

var H = require("../support/harness");
var child = require("child_process");
var fs = require("fs");
var path = require("path");

var TESTS = process.env.PRISTINE_TESTS || "/opt/pristine-tests/tests";
var FILES = [
    "api_textformat.js",
    "api_enum.js",
    "api_object.js",
    "api_descriptor.js",
    "api_util.js"
].map(function (f) { return path.join(TESTS, f); });

H.test("the project's own tests for the affected area still pass", function () {
    FILES.forEach(function (f) {
        H.ok(fs.existsSync(f), "pristine project test missing: " + f);
    });
    var tape = path.join(H.APP, "node_modules", "tape", "bin", "tape");
    H.ok(fs.existsSync(tape), "project test runner missing");
    var res = child.spawnSync(process.execPath, [
        tape,
        "-r", path.join(H.APP, "lib", "tape-adapter"),
        FILES[0], FILES[1], FILES[2], FILES[3], FILES[4]
    ], { cwd: H.APP, encoding: "utf8", timeout: 300000 });
    var tail = String(res.stdout || "").split("\n").slice(-12).join("\n");
    H.strictEqual(res.status, 0, "project tests failed:\n" + tail + "\n" + String(res.stderr || "").slice(0, 800));
    H.ok(String(res.stdout).indexOf("# fail") < 0, "project tests reported failures:\n" + tail);
});
