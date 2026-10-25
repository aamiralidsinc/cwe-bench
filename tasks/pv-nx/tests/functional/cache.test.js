'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { tempRoot, makeCache, writeArtifact } = require('../support/nx');
const { tarGz } = require('../support/tar');
const { withRemote } = require('../support/http');

function resultFor(outputsPath, extra = {}) {
  return { code: 0, terminalOutput: '', outputsPath, size: 0, ...extra };
}

test('fun-cache: a directory output round-trips through the cache', async () => {
  const root = tempRoot('fun-roundtrip');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(path.join(ws, 'dist', 'nested'), { recursive: true });
  fs.writeFileSync(path.join(ws, 'dist', 'main.js'), 'console.log(1)');
  fs.writeFileSync(path.join(ws, 'dist', 'nested', 'data.json'), '{"a":1}');
  const cache = makeCache(ws, cacheDir);

  cache.put('f1', 'built in 10ms', ['dist'], 0);
  fs.rmSync(path.join(ws, 'dist'), { recursive: true, force: true });
  const stored = cache.get('f1');
  cache.copyFilesFromCache(stored, ['dist']);

  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'main.js'), 'utf8'), 'console.log(1)');
  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'nested', 'data.json'), 'utf8'), '{"a":1}');
});

test('fun-cache: several declared outputs are restored together', async () => {
  const root = tempRoot('fun-multi');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(path.join(ws, 'app'), { recursive: true });
  fs.mkdirSync(path.join(ws, 'lake'), { recursive: true });
  fs.writeFileSync(path.join(ws, 'app', 'main.js'), 'app');
  fs.writeFileSync(path.join(ws, 'lake', 'part.parquet'), 'lake');
  const cache = makeCache(ws, cacheDir);

  cache.put('f2', 'done', ['app', 'lake'], 0);
  fs.rmSync(path.join(ws, 'app'), { recursive: true, force: true });
  fs.rmSync(path.join(ws, 'lake'), { recursive: true, force: true });
  const stored = cache.get('f2');
  cache.copyFilesFromCache(stored, ['app', 'lake']);

  assert.equal(fs.readFileSync(path.join(ws, 'app', 'main.js'), 'utf8'), 'app');
  assert.equal(fs.readFileSync(path.join(ws, 'lake', 'part.parquet'), 'utf8'), 'lake');
});

test('fun-cache: a glob output restores every matching file', async () => {
  const root = tempRoot('fun-glob');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(path.join(ws, 'dist'), { recursive: true });
  fs.writeFileSync(path.join(ws, 'dist', 'a.js'), 'a');
  fs.writeFileSync(path.join(ws, 'dist', 'b.css'), 'b');
  const cache = makeCache(ws, cacheDir);

  cache.put('f3', 'done', ['dist/**/*.js'], 0);
  fs.rmSync(path.join(ws, 'dist'), { recursive: true, force: true });
  const stored = cache.get('f3');
  cache.copyFilesFromCache(stored, ['dist/**/*.js']);

  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'a.js'), 'utf8'), 'a');
});

test('fun-cache: a symlinked output file is restored as a link', async () => {
  const root = tempRoot('fun-symlink-file');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(path.join(ws, 'dist'), { recursive: true });
  fs.writeFileSync(path.join(ws, 'dist', 'main.js'), 'linked-content');
  fs.symlinkSync('main.js', path.join(ws, 'dist', 'alias.js'));
  const cache = makeCache(ws, cacheDir);

  cache.put('f4', 'done', ['dist/main.js', 'dist/alias.js'], 0);
  fs.rmSync(path.join(ws, 'dist'), { recursive: true, force: true });
  const stored = cache.get('f4');
  cache.copyFilesFromCache(stored, ['dist/main.js', 'dist/alias.js']);

  const alias = path.join(ws, 'dist', 'alias.js');
  assert.equal(fs.lstatSync(alias).isSymbolicLink(), true, 'a link output keeps being a link');
  assert.equal(fs.readlinkSync(alias), 'main.js');
  assert.equal(fs.readFileSync(alias, 'utf8'), 'linked-content');
});

test('fun-cache: a link that points elsewhere is restored as a pointer, not followed', async () => {
  const root = tempRoot('fun-symlink-out');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(ws, { recursive: true });
  fs.mkdirSync(outside, { recursive: true });
  fs.writeFileSync(path.join(outside, 'shared.txt'), 'shared');
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'f5', { dist: { symlink: outside } });

  cache.copyFilesFromCache(resultFor(artifact), ['dist']);

  const link = path.join(ws, 'dist');
  assert.equal(fs.lstatSync(link).isSymbolicLink(), true, 'a link output is recreated verbatim');
  assert.equal(fs.readlinkSync(link), outside);
  assert.equal(fs.existsSync(path.join(ws, 'dist', 'shared.txt')), true, 'reading through the restored link still works');
  assert.equal(fs.readFileSync(path.join(outside, 'shared.txt'), 'utf8'), 'shared');
});

test('fun-cache: a declared output missing from the artifact is skipped', async () => {
  const root = tempRoot('fun-missing');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(ws, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'f6', { 'dist/a.txt': 'a' });

  cache.copyFilesFromCache(resultFor(artifact), ['dist', 'not-produced']);

  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'a.txt'), 'utf8'), 'a');
  assert.equal(fs.existsSync(path.join(ws, 'not-produced')), false);
});

test('fun-cache: applying a remote result records its output and exit code', async () => {
  const root = tempRoot('fun-apply');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(ws, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'f7', {});

  cache.applyRemoteCacheResults(
    'f7',
    resultFor(artifact, { code: 0, terminalOutput: 'remote output' }),
    []
  );

  const stored = cache.get('f7');
  assert.equal(stored.code, 0);
  assert.equal(stored.terminalOutput, 'remote output');
});

test('fun-cache: a normal remote artifact extracts and reports its result', async () => {
  const root = tempRoot('fun-remote');
  const cacheDir = path.join(root, 'cache');
  const artifact = tarGz([
    { name: 'dist/main.js', data: 'console.log(1)' },
    { name: 'code', data: Buffer.from([0, 0, 0, 0]) },
    { name: 'terminalOutput', data: 'build complete' },
  ]);

  await withRemote({ '/v1/cache/f8': artifact }, async (remote) => {
    const result = await remote.retrieve('f8', cacheDir);
    assert.equal(result.code, 0);
    assert.equal(result.terminalOutput, 'build complete');
    assert.equal(
      fs.readFileSync(path.join(result.outputsPath, 'dist', 'main.js'), 'utf8'),
      'console.log(1)'
    );
  });
});
