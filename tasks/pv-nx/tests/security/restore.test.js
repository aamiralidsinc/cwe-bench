'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { tempRoot, makeCache, writeArtifact } = require('../support/nx');
const { tarGz } = require('../support/tar');
const { withRemote } = require('../support/http');

function resultFor(outputsPath) {
  return { code: 0, terminalOutput: '', outputsPath, size: 0 };
}

test('sec-restore: only the declared outputs are restored', async () => {
  const root = tempRoot('restore-declared');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(ws, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'r1', {
    'dist/main.js': 'ok',
    '.git/hooks/pre-commit': '#!/bin/sh\nevil',
    'package.json': '{"evil":true}',
  });

  cache.copyFilesFromCache(resultFor(artifact), ['dist']);

  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'main.js'), 'utf8'), 'ok');
  assert.equal(fs.existsSync(path.join(ws, '.git', 'hooks', 'pre-commit')), false,
    'a file that is not a declared output must not be restored');
  assert.equal(fs.existsSync(path.join(ws, 'package.json')), false,
    'a file that is not a declared output must not be restored');
});

test('sec-restore: restoring does not write through an existing workspace link', async () => {
  const root = tempRoot('restore-writethrough');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(ws, { recursive: true });
  fs.mkdirSync(outside, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'r2', { 'dist/payload.js': 'PWNED' });
  fs.symlinkSync(outside, path.join(ws, 'dist'));

  cache.copyFilesFromCache(resultFor(artifact), ['dist/payload.js']);

  assert.equal(fs.existsSync(path.join(outside, 'payload.js')), false,
    'nothing may be written through a pre-existing link in the workspace');
  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'payload.js'), 'utf8'), 'PWNED',
    'the declared output itself is still restored inside the workspace');
});

test('sec-restore: an absolute output outside the workspace is not applied', async () => {
  const root = tempRoot('restore-abs-outside');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(ws, { recursive: true });
  const victim = path.join(root, 'victim.txt');
  fs.writeFileSync(victim, 'KEEP-ME');
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'r3', { 'dist/a.txt': 'x' });

  try {
    cache.copyFilesFromCache(resultFor(artifact), [victim]);
  } catch {
    /* refusing is an acceptable outcome */
  }

  assert.equal(fs.readFileSync(victim, 'utf8'), 'KEEP-ME',
    'a path outside the workspace must not be touched, even by a refusal');
});


test('sec-restore: a remote artifact is applied only within the declared outputs', async () => {
  const root = tempRoot('restore-remote');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(ws, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = tarGz([
    { name: 'dist/app.js', data: 'ok' },
    { name: '.git/hooks/pre-commit', data: '#!/bin/sh\nevil' },
    { name: 'code', data: Buffer.from([0, 0, 0, 0]) },
    { name: 'terminalOutput', data: 'built' },
  ]);

  await withRemote({ '/v1/cache/r5': artifact }, async (remote) => {
    const result = await remote.retrieve('r5', cacheDir);
    cache.applyRemoteCacheResults('r5', result, ['dist']);
  });

  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'app.js'), 'utf8'), 'ok');
  assert.equal(fs.existsSync(path.join(ws, '.git', 'hooks', 'pre-commit')), false,
    'applying a remote result must restore only the declared outputs');
});
