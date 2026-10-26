"use strict";
// Child-process probe. It builds an archive, performs exactly one public read, and reports the
// bytes returned and the growth of live ArrayBuffer memory. It decides nothing: the assertions
// live in the parent check, so hardening the library cannot change what is measured.
//
//   node driver.js <productRoot> <sync|async|readFile> <specJSON>
//
// specJSON: { method: 0|8, declared: <header uncompressed size>, realMB: <true output size>,
//             fill: <byte>, crc: "real"|"empty" }
const path = require("path");
const zlib = require("zlib");
const { craft, crc32 } = require("./lib.js");

const root = process.argv[2];
const scenario = process.argv[3];
const spec = JSON.parse(process.argv[4]);
const Zip = require(path.join(root, "adm-zip.js"));

const real = Buffer.alloc(spec.realMB * 1024 * 1024, spec.fill === undefined ? 0x41 : spec.fill);
const content = spec.method === 8 ? zlib.deflateRawSync(real) : real;
const crc = spec.crc === "empty" ? 0 : crc32(real);
const archive = craft({ name: Buffer.from("a"), method: spec.method, content: content, declaredSize: spec.declared, crc: crc });
const zip = new Zip(archive);
const entry = zip.getEntries()[0];

const before = process.memoryUsage().arrayBuffers;
let reported = false;

function report(err, out) {
    if (reported) return;
    reported = true;
    const after = process.memoryUsage().arrayBuffers;
    process.stdout.write(
        JSON.stringify({
            error: err ? String(err.message || err) : null,
            outLen: out && typeof out.length === "number" ? out.length : null,
            abMB: Math.round(((after - before) / 1048576) * 10) / 10
        }) + "\n"
    );
}

// A reader that never settles must not hang the parent forever.
setTimeout(() => {
    if (!reported) {
        reported = true;
        process.stdout.write(JSON.stringify({ error: null, outLen: null, abMB: -1, hang: true }) + "\n");
        process.exit(0);
    }
}, 45000).unref();

try {
    if (scenario === "sync") {
        let out;
        try {
            out = entry.getData();
        } catch (e) {
            report(e);
            process.exit(0);
        }
        report(null, out);
    } else if (scenario === "async") {
        entry.getDataAsync(function (out, err) {
            report(err, out);
        });
    } else if (scenario === "readFile") {
        let out;
        try {
            out = zip.readFile("a");
        } catch (e) {
            report(e);
            process.exit(0);
        }
        report(null, out);
    } else {
        report(new Error("unknown scenario " + scenario));
    }
} catch (e) {
    report(e);
    process.exit(0);
}
