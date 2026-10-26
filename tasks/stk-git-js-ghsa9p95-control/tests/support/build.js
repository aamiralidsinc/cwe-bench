#!/usr/bin/env node
'use strict';

/*
 * Bundle the submitted library sources into one CommonJS file the hidden runner can require.
 * The project's own entry point is src/index.js; esbuild resolves the TypeScript modules it
 * imports. Only the library's published runtime dependencies stay external (the verifier image
 * provides them under /opt/verifier/node_modules).
 */

const path = require('path');
const esbuild = require('esbuild');

const srcDir = process.argv[2] || '/workspace/simple-git';
const out = process.argv[3] || '/workspace/.htests/product.cjs';

esbuild.buildSync({
  absWorkingDir: srcDir,
  entryPoints: [path.join(srcDir, 'src', 'index.js')],
  bundle: true,
  platform: 'node',
  format: 'cjs',
  target: 'node20',
  outfile: out,
  logLevel: 'error',
  external: ['debug', '@kwsites/file-exists', '@kwsites/promise-deferred'],
});

console.log('bundled ' + out);
