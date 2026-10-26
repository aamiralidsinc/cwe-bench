"use strict";
// Hidden functional checks: legitimate archives must keep reading and extracting exactly as
// they do now. Archive bytes are built here; nothing is taken from the library under test.
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { craft, craftMulti, crc32, deflate } = require("./lib.js");

const ROOT = process.env.PRODUCT_ROOT || "/workspace";
const AdmZip = require(path.join(ROOT, "adm-zip.js"));

function readAsync(zip, name) {
    return new Promise((resolve) => {
        zip.readFileAsync(name, function (data, err) {
            resolve({ data: data, err: err });
        });
    });
}

function entryAsync(entry) {
    return new Promise((resolve) => {
        entry.getDataAsync(function (data, err) {
            resolve({ data: data, err: err });
        });
    });
}

describe("adm-zip legitimate reads", () => {
    it("TestFunc_EmptyDeflatedEntry", async function () {
        this.timeout(60000);
        const archive = craft({
            name: Buffer.from("empty.txt"),
            method: 8,
            content: deflate(Buffer.alloc(0)),
            declaredSize: 0,
            crc: 0
        });
        const zip = new AdmZip(archive);
        const viaEntry = zip.getEntries()[0].getData();
        assert.ok(Buffer.isBuffer(viaEntry) && viaEntry.length === 0, "synchronous read of an empty entry");
        const async = await entryAsync(zip.getEntries()[0]);
        assert.ok(!async.err, "asynchronous read of an empty entry reported: " + async.err);
        assert.ok(Buffer.isBuffer(async.data) && async.data.length === 0, "asynchronous read of an empty entry");
        const viaName = zip.readFile("empty.txt");
        assert.ok(Buffer.isBuffer(viaName) && viaName.length === 0, "read by name of an empty entry");
    });

    it("TestFunc_LargeCompressibleRead", async function () {
        this.timeout(120000);
        const real = Buffer.alloc(64 * 1024 * 1024, 0x5a);
        const archive = craft({
            name: Buffer.from("zeros.bin"),
            method: 8,
            content: deflate(real),
            declaredSize: real.length,
            crc: crc32(real)
        });
        const zip = new AdmZip(archive);
        const sync = zip.getEntries()[0].getData();
        assert.ok(Buffer.isBuffer(sync) && sync.equals(real), "synchronous read of a highly compressible entry");
        const async = await entryAsync(zip.getEntries()[0]);
        assert.ok(!async.err, "asynchronous read reported: " + async.err);
        assert.ok(Buffer.isBuffer(async.data) && async.data.equals(real), "asynchronous read of a highly compressible entry");
        const byName = zip.readFile("zeros.bin");
        assert.ok(Buffer.isBuffer(byName) && byName.equals(real), "read by name of a highly compressible entry");
    });

    it("TestFunc_LargeStoredEntry", function () {
        this.timeout(120000);
        const real = Buffer.alloc(32 * 1024 * 1024, 0x7c);
        const archive = craft({
            name: Buffer.from("plain.bin"),
            method: 0,
            content: real,
            declaredSize: real.length,
            crc: crc32(real)
        });
        const zip = new AdmZip(archive);
        const sync = zip.getEntries()[0].getData();
        assert.ok(Buffer.isBuffer(sync) && sync.equals(real), "synchronous read of a large stored entry");
        const byName = zip.readFile("plain.bin");
        assert.ok(Buffer.isBuffer(byName) && byName.equals(real), "read by name of a large stored entry");
    });

    it("TestFunc_ExtractAllToAsync", function (done) {
        this.timeout(120000);
        const empty = Buffer.alloc(0);
        const compressible = Buffer.alloc(4 * 1024 * 1024, 0x33);
        const plain = Buffer.alloc(1024 * 1024, 0x11);
        const archive = craftMulti([
            { name: "empty.txt", data: empty, method: 8 },
            { name: "zeros.bin", data: compressible, method: 8 },
            { name: "plain.bin", data: plain, method: 0 }
        ]);
        const zip = new AdmZip(archive);
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), "admzip-extract-"));
        zip.extractAllToAsync(dir, true, false, function (err) {
            try {
                assert.ok(!err, "extraction reported: " + err);
                assert.strictEqual(fs.readFileSync(path.join(dir, "empty.txt")).length, 0, "empty file extracted");
                assert.ok(fs.readFileSync(path.join(dir, "zeros.bin")).equals(compressible), "compressible file extracted");
                assert.ok(fs.readFileSync(path.join(dir, "plain.bin")).equals(plain), "stored file extracted");
                done();
            } catch (e) {
                done(e);
            } finally {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        });
    });
});
