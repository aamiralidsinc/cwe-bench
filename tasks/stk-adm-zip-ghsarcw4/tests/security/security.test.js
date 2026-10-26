"use strict";
// Hidden security checks: each drives one public read of a crafted archive in a fresh child
// process and asserts that the read neither reports more data than the entry declares nor
// allocates memory from a declared size. The child reports measurements only.
const assert = require("assert");
const path = require("path");
const { execFileSync } = require("child_process");

const DRIVER = path.join(__dirname, "driver.js");
const ROOT = process.env.PRODUCT_ROOT || "/workspace";
const MIB = 1024 * 1024;

function probe(scenario, spec) {
    let out;
    try {
        out = execFileSync(process.execPath, [DRIVER, ROOT, scenario, JSON.stringify(spec)], {
            cwd: __dirname,
            encoding: "utf8",
            timeout: 120000,
            killSignal: "SIGKILL",
            stdio: ["ignore", "pipe", "pipe"]
        });
    } catch (e) {
        assert.fail("the read crashed or did not finish: " + (e.stderr || e.message || e));
    }
    const line = String(out).trim().split("\n").filter(Boolean).pop();
    assert.ok(line, "the read produced no result");
    try {
        return JSON.parse(line);
    } catch (e) {
        assert.fail("the read produced no parseable result: " + line.slice(0, 300));
    }
}

// A read is blocked when it either reports a failure or stays within the declared size, and
// when the memory it allocates is far below the size the archive merely claims.
function blocked(res, declared, boundMiB) {
    assert.ok(!res.hang, "the read did not settle");
    assert.ok(
        res.abMB <= boundMiB,
        "the read allocated " + res.abMB + " MiB for an archive that carries far less (limit " + boundMiB + " MiB)"
    );
    if (res.error) return;
    assert.ok(
        res.outLen !== null && res.outLen <= declared,
        "the read produced " + res.outLen + " bytes for an entry that declares " + declared
    );
}

describe("adm-zip decompression bounds", () => {
    it("TestSec_SyncZeroDeclarationBounded", function () {
        this.timeout(120000);
        // A DEFLATED entry that declares 0 uncompressed bytes while its stream expands to 64 MiB.
        const res = probe("sync", { method: 8, declared: 0, realMB: 64, fill: 0x41, crc: "empty" });
        blocked(res, 0, 32);
    });

    it("TestSec_ReadFileZeroDeclarationBounded", function () {
        this.timeout(120000);
        const res = probe("readFile", { method: 8, declared: 0, realMB: 64, fill: 0x42, crc: "empty" });
        blocked(res, 0, 32);
    });

    it("TestSec_AsyncDeclarationBounded", function () {
        this.timeout(120000);
        // The asynchronous read of an entry whose declared size (1 KiB) is far below its output.
        const res = probe("async", { method: 8, declared: 1024, realMB: 64, fill: 0x43, crc: "real" });
        blocked(res, 1024, 32);
    });

    it("TestSec_AsyncZeroDeclarationBounded", function () {
        this.timeout(120000);
        const res = probe("async", { method: 8, declared: 0, realMB: 64, fill: 0x44, crc: "empty" });
        blocked(res, 0, 32);
    });

    it("TestSec_StoredDeclaredSizeNotPreallocated", function () {
        this.timeout(120000);
        // A STORED entry carrying 1 byte but declaring 1 GiB must not allocate the claim.
        const res = probe("sync", { method: 0, declared: 1024 * MIB, realMB: 1, fill: 0x45, crc: "real" });
        assert.ok(!res.hang, "the read did not settle");
        assert.ok(
            res.abMB <= 64,
            "the read allocated " + res.abMB + " MiB from a declared size alone (limit 64 MiB)"
        );
    });

    it("TestSec_DeflatedDeclaredSizeNotPreallocated", function () {
        this.timeout(120000);
        // A DEFLATED entry carrying one byte but declaring 1 GiB must not allocate the claim.
        const res = probe("sync", { method: 8, declared: 1024 * MIB, realMB: 1, fill: 0x46, crc: "real" });
        assert.ok(!res.hang, "the read did not settle");
        assert.ok(
            res.abMB <= 64,
            "the read allocated " + res.abMB + " MiB from a declared size alone (limit 64 MiB)"
        );
    });
});
