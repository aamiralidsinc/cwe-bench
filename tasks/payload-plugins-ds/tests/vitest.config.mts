import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vitest/config'

// The product lives in /workspace (the solver's tree). This hidden suite is
// copied to /workspace/.htests and run from there with the project's dependency
// tree. `next/cache.js` is replaced by a contract-matched in-memory cache so the
// product's shared-cache behaviour can be exercised without a Next server.
const cacheStub = fileURLToPath(new URL('./harness/nextCacheStub.ts', import.meta.url))
const workspace = process.env.WORKSPACE_DIR || '/workspace'

export default defineConfig({
  cacheDir: '/tmp/payload-plugins-vite-hidden',
  resolve: {
    alias: [{ find: /^next\/cache\.js$/, replacement: cacheStub }],
  },
  server: {
    fs: { allow: [workspace] },
  },
  test: {
    environment: 'node',
    fileParallelism: false,
    globals: true,
    include: ['security/**/*.test.ts', 'functional/**/*.test.ts'],
    pool: 'forks',
    setupFiles: ['./setup.ts'],
    testTimeout: 60000,
  },
})
