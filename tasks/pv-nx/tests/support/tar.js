'use strict';

const zlib = require('node:zlib');

function octal(buf, off, len, value) {
  const s = value.toString(8).padStart(len - 1, '0') + '\0';
  buf.write(s, off, len, 'ascii');
}

function header(name, { type = '0', size = 0, link = '', mode = 0o644 } = {}) {
  const b = Buffer.alloc(512);
  const nb = Buffer.from(name, 'utf8');
  if (nb.length > 100) throw new Error('entry name too long for this helper');
  nb.copy(b, 0);
  octal(b, 100, 8, mode);
  octal(b, 108, 8, 0);
  octal(b, 116, 8, 0);
  octal(b, 124, 12, size);
  octal(b, 136, 12, 0);
  b.write(type, 156, 1, 'ascii');
  if (link) Buffer.from(link, 'utf8').copy(b, 157);
  b.write('ustar\0', 257, 6, 'ascii');
  b.write('00', 263, 2, 'ascii');
  b.fill(0x20, 148, 156);
  let sum = 0;
  for (const x of b) sum += x;
  b.write(sum.toString(8).padStart(6, '0') + '\0 ', 148, 8, 'ascii');
  return b;
}

function entry(name, data, opts = {}) {
  const buf = Buffer.isBuffer(data) ? data : Buffer.from(data || '');
  const special = opts.type === '5' || opts.type === '2' || opts.type === '1';
  const h = header(name, { ...opts, size: special ? 0 : buf.length });
  if (special) return h;
  const pad = Buffer.alloc((512 - (buf.length % 512)) % 512);
  return Buffer.concat([h, buf, pad]);
}

function tarGz(entries) {
  const parts = entries.map((e) => entry(e.name, e.data, e.opts || {}));
  parts.push(Buffer.alloc(1024));
  return zlib.gzipSync(Buffer.concat(parts));
}

module.exports = { tarGz };
