import { defineConfig } from 'vitest/config'
import path from 'node:path'

const ROOT = process.env.HTESTS_DIR || '/workspace/.htests'
const WORKSPACE = process.env.WORKSPACE_DIR || '/workspace'

export default defineConfig({
  cacheDir: path.join(ROOT, '.vite-cache'),
  resolve: { alias: { '@': path.join(WORKSPACE, 'js') } },
  server: { fs: { allow: [WORKSPACE, ROOT] } },
  test: {
    root: ROOT,
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'http://localhost:3000/' } },
    setupFiles: [path.join(ROOT, 'setup.mjs')],
    include: ['**/*.test.mjs'],
    testTimeout: 20000,
    hookTimeout: 20000,
  },
})
