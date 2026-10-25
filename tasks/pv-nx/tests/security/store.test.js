'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { tempRoot, makeCache, readAllFiles } = require('../support/nx');

test('sec-store: a linked output directory is not read through when storing', async () => {
  const root = tempRoot('store-linkdir');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(ws, { recursive: true });
  fs.mkdirSync(outside, { recursive: true });
  fs.writeFileSync(path.join(outside, 'secret.txt'), 'OUTSIDE-CONTENT');
  fs.symlinkSync(outside, path.join(ws, 'linkdir'));
  const cache = makeCache(ws, cacheDir);

  cache.put('s1', 'out', ['linkdir'], 0);

  const entry = path.join(cacheDir, 's1', 'linkdir');
  const stored = readAllFiles(path.join(cacheDir, 's1')).some(
    (file) => fs.lstatSync(file).isFile() && fs.readFileSync(file, 'utf8') === 'OUTSIDE-CONTENT'
  );
  assert.equal(stored, false, 'content behind a link is not part of the declared output');
  assert.equal(fs.lstatSync(entry).isSymbolicLink(), true, 'the link itself is what gets stored');
});

test('sec-store: an output that climbs out of the workspace is not stored outside the entry', async () => {
  const root = tempRoot('store-climb');
  const ws = path.join(root, 'proj');
  const cacheDir = path.join(ws, '.nx', 'cache');
  fs.mkdirSync(ws, { recursive: true });
  fs.writeFileSync(path.join(root, 'stray.txt'), 'STRAY-CONTENT');
  const cache = makeCache(ws, cacheDir);

  try {
    cache.put('s2', 'out', ['../stray.txt'], 0);
  } catch {
    /* refusing is an acceptable outcome */
  }

  assert.equal(fs.existsSync(path.join(cacheDir, 'stray.txt')), false,
    'no copy may land beside the cache entry');
  assert.equal(fs.existsSync(path.join(ws, '.nx', 'stray.txt')), false);
  assert.equal(fs.readFileSync(path.join(root, 'stray.txt'), 'utf8'), 'STRAY-CONTENT');
});

test('sec-store: an absolute output that resolves inside the workspace is still stored', async () => {
  const root = tempRoot('store-abs-inside');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(path.join(ws, 'dist'), { recursive: true });
  fs.writeFileSync(path.join(ws, 'dist', 'a.txt'), 'from-workspace');
  const cache = makeCache(ws, cacheDir);

  cache.put('s3', 'out', [path.join(ws, 'dist')], 0);

  assert.equal(fs.readFileSync(path.join(cacheDir, 's3', 'dist', 'a.txt'), 'utf8'), 'from-workspace',
    'an absolute path that resolves inside the workspace remains a valid output');
});
