"use strict";
// Independent ZIP construction helpers for the hidden checks. Only Node built-ins are used:
// the archive bytes and the CRC are computed here, never through the library under test.
const zlib = require("zlib");

const u16 = (n) => {
    const b = Buffer.alloc(2);
    b.writeUInt16LE(n >>> 0);
    return b;
};
const u32 = (n) => {
    const b = Buffer.alloc(4);
    b.writeUInt32LE(n >>> 0);
    return b;
};

// CRC-32 (IEEE 802.3), table built here so the product's own helper is never involved.
const CRC_TABLE = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
        let c = n;
        for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
        t[n] = c >>> 0;
    }
    return t;
})();
function crc32(buf) {
    let c = 0xffffffff;
    for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
}

function localEntry(name, method, content, crc, csize, usize) {
    return Buffer.concat([
        u32(0x04034b50),
        u16(20),
        u16(0),
        u16(method),
        u16(0),
        u16(0),
        u32(crc),
        u32(csize),
        u32(usize),
        u16(name.length),
        u16(0),
        name,
        content
    ]);
}

function centralEntry(name, method, crc, csize, usize, offset) {
    return Buffer.concat([
        u32(0x02014b50),
        u16(20),
        u16(20),
        u16(0),
        u16(method),
        u16(0),
        u16(0),
        u32(crc),
        u32(csize),
        u32(usize),
        u16(name.length),
        u16(0),
        u16(0),
        u16(0),
        u16(0),
        u32(0),
        u32(offset),
        name
    ]);
}

// One entry, with the declared sizes written into both headers.
function craft({ name, method, content, declaredSize, crc, compressedSize }) {
    name = name || Buffer.from("a");
    const csize = compressedSize === undefined ? content.length : compressedSize;
    const lfh = localEntry(name, method, content, crc >>> 0, csize, declaredSize);
    const cd = centralEntry(name, method, crc >>> 0, csize, declaredSize, 0);
    const eocd = Buffer.concat([
        u32(0x06054b50),
        u16(0),
        u16(0),
        u16(1),
        u16(1),
        u32(cd.length),
        u32(lfh.length),
        u16(0)
    ]);
    return Buffer.concat([lfh, cd, eocd]);
}

// Several entries; each is { name, data, method } and is written with honest header values.
function craftMulti(entries) {
    const locals = [];
    const centrals = [];
    let offset = 0;
    for (const e of entries) {
        const name = Buffer.from(e.name);
        const data = Buffer.isBuffer(e.data) ? e.data : Buffer.from(e.data);
        const method = e.method === undefined ? 0 : e.method;
        const content = method === 8 ? zlib.deflateRawSync(data) : data;
        const crc = crc32(data);
        const local = localEntry(name, method, content, crc, content.length, data.length);
        centrals.push(centralEntry(name, method, crc, content.length, data.length, offset));
        locals.push(local);
        offset += local.length;
    }
    const cd = Buffer.concat(centrals);
    const eocd = Buffer.concat([
        u32(0x06054b50),
        u16(0),
        u16(0),
        u16(entries.length),
        u16(entries.length),
        u32(cd.length),
        u32(offset),
        u16(0)
    ]);
    return Buffer.concat([...locals, cd, eocd]);
}

module.exports = { craft, craftMulti, crc32, deflate: zlib.deflateRawSync };
