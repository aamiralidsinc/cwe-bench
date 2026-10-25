'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { tempRoot, readAllFiles } = require('../support/nx');
const { tarGz } = require('../support/tar');
const { withRemote } = require('../support/http');

const CODE0 = { name: 'code', data: Buffer.from([0, 0, 0, 0]) };
const TERM = { name: 'terminalOutput', data: '' };

async function retrieveInto(cacheDir, hash, artifact) {
  return withRemote({ [`/v1/cache/${hash}`]: artifact }, async (remote) => {
    try {
      return { result: await remote.retrieve(hash, cacheDir) };
    } catch (error) {
      return { error };
    }
  });
}

test('sec-extract: parent-directory entries stay inside the cache entry', async () => {
  const root = tempRoot('extract-parent');
  const cacheDir = path.join(root, 'cache');
  const escaped = path.join(root, 'escaped.txt');
  const artifact = tarGz([
    { name: '../../escaped.txt', data: 'PWNED' },
    CODE0,
    TERM,
  ]);

  await retrieveInto(cacheDir, 'hash1', artifact);

  assert.equal(fs.existsSync(escaped), false, 'no file may appear above the cache entry');
});

test('sec-extract: absolute entry names stay inside the cache entry', async () => {
  const root = tempRoot('extract-abs');
  const cacheDir = path.join(root, 'cache');
  const escaped = path.join(root, 'absolute-target.txt');
  const artifact = tarGz([
    { name: escaped, data: 'PWNED' },
    CODE0,
    TERM,
  ]);

  await retrieveInto(cacheDir, 'hash2', artifact);

  assert.equal(fs.existsSync(escaped), false, 'an absolute entry must not be written at its absolute path');
});

test('sec-extract: a symlink entry cannot be used to write outside', async () => {
  const root = tempRoot('extract-symlink');
  const cacheDir = path.join(root, 'cache');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(outside, { recursive: true });
  const artifact = tarGz([
    { name: 'evil', data: '', opts: { type: '2', link: outside } },
    { name: 'evil/through.txt', data: 'PWNED' },
    CODE0,
    TERM,
  ]);

  await retrieveInto(cacheDir, 'hash3', artifact);

  assert.equal(fs.existsSync(path.join(outside, 'through.txt')), false, 'no write may pass through a link entry');
});

test('sec-extract: a hardlink entry cannot pull in outside content', async () => {
  const root = tempRoot('extract-hardlink');
  const cacheDir = path.join(root, 'cache');
  const secret = path.join(root, 'secret.txt');
  fs.writeFileSync(secret, 'TOP-SECRET-VALUE');
  const artifact = tarGz([
    { name: 'borrowed', data: '', opts: { type: '1', link: secret } },
    CODE0,
    TERM,
  ]);

  await retrieveInto(cacheDir, 'hash4', artifact);

  const entryDir = path.join(cacheDir, 'hash4');
  const leaked = readAllFiles(entryDir).some(
    (file) => fs.lstatSync(file).isFile() && fs.readFileSync(file, 'utf8') === 'TOP-SECRET-VALUE'
  );
  assert.equal(leaked, false, 'an entry may not reference content it did not carry');
});

test('sec-extract: traversal split across separators is contained too', async () => {
  const root = tempRoot('extract-nested');
  const cacheDir = path.join(root, 'cache');
  const escaped = path.join(root, 'nested-escaped.txt');
  const artifact = tarGz([
    { name: 'dist/../../../nested-escaped.txt', data: 'PWNED' },
    CODE0,
    TERM,
  ]);

  await retrieveInto(cacheDir, 'hash5', artifact);

  assert.equal(fs.existsSync(escaped), false, 'a nested traversal must not escape the cache entry');
});

test('sec-extract: the legacy cache route is contained as well', async () => {
  const root = tempRoot('extract-legacy');
  const cacheDir = path.join(root, 'cache');
  const escaped = path.join(root, 'legacy-escaped.txt');
  const artifact = tarGz([
    { name: '../../legacy-escaped.txt', data: 'PWNED' },
    CODE0,
    TERM,
  ]);

  await withRemote({ '/api/v1/cache/legacyhash': artifact }, async (remote) => {
    try {
      await remote.retrieve('legacyhash', cacheDir);
    } catch {
      /* a refusal is an acceptable outcome */
    }
  });

  assert.equal(fs.existsSync(escaped), false, 'an artifact served on the legacy route must not escape either');
});
