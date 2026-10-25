'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

let loaded;

function native() {
  if (!loaded) {
    const addon = process.env.NX_ADDON;
    if (!addon) throw new Error('NX_ADDON is not set');
    const mod = { exports: {} };
    process.dlopen(mod, addon);
    loaded = mod.exports;
  }
  return loaded;
}

function tempRoot(label) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `pv-nx-${label}-`));
}

function makeCache(workspace, cacheDir) {
  const dbName = 'db-' + Math.random().toString(16).slice(2);
  const db = native().connectToNxDb(cacheDir, dbName);
  const NxCache = native().NxCache;
  return new NxCache(workspace, cacheDir, db, false, 0);
}

/// Create a cache artifact directory for `hash` from a plain description.
/// Values may be strings, Buffers, or {symlink: target}.
function writeArtifact(cacheDir, hash, files) {
  const entryDir = path.join(cacheDir, hash);
  fs.mkdirSync(entryDir, { recursive: true });
  for (const [rel, value] of Object.entries(files)) {
    const dest = path.join(entryDir, rel);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    if (value && typeof value === 'object' && !Buffer.isBuffer(value) && value.symlink) {
      fs.symlinkSync(value.symlink, dest);
    } else {
      fs.writeFileSync(dest, value);
    }
  }
  return entryDir;
}

function readAllFiles(dir) {
  const out = [];
  const walk = (d) => {
    for (const name of fs.readdirSync(d)) {
      const p = path.join(d, name);
      const st = fs.lstatSync(p);
      if (st.isDirectory()) walk(p);
      else out.push(p);
    }
  };
  if (fs.existsSync(dir)) walk(dir);
  return out;
}

module.exports = { native, tempRoot, makeCache, writeArtifact, readAllFiles };
