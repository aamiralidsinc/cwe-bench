'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { tempRoot, makeCache, writeArtifact } = require('../support/nx');

function resultFor(outputsPath) {
  return { code: 0, terminalOutput: '', outputsPath, size: 0 };
}

test('sec-batch: a batch restore writes only the declared outputs', async () => {
  const root = tempRoot('batch-declared');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  fs.mkdirSync(ws, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'b1', {
    'dist/main.js': 'ok',
    '.git/hooks/pre-commit': '#!/bin/sh\nevil',
    'package.json': '{"evil":true}',
  });

  cache.applyRemoteCacheResultsBatch(['b1'], [resultFor(artifact)], [['dist']]);

  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'main.js'), 'utf8'), 'ok');
  assert.equal(fs.existsSync(path.join(ws, '.git', 'hooks', 'pre-commit')), false,
    'a batched restore must not write undeclared files');
  assert.equal(fs.existsSync(path.join(ws, 'package.json')), false);
});

test('sec-batch: a batch restore does not write through an existing workspace link', async () => {
  const root = tempRoot('batch-writethrough');
  const ws = path.join(root, 'ws');
  const cacheDir = path.join(root, 'cache');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(ws, { recursive: true });
  fs.mkdirSync(outside, { recursive: true });
  const cache = makeCache(ws, cacheDir);
  const artifact = writeArtifact(cacheDir, 'b2', { 'dist/payload.js': 'PWNED' });
  fs.symlinkSync(outside, path.join(ws, 'dist'));

  cache.applyRemoteCacheResultsBatch(['b2'], [resultFor(artifact)], [['dist/payload.js']]);

  assert.equal(fs.existsSync(path.join(outside, 'payload.js')), false,
    'a batched restore must not write outside through a link');
});
