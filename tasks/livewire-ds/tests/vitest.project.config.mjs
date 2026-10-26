import { defineConfig } from 'vitest/config'
import path from 'node:path'

const ROOT = process.env.HTESTS_DIR || '/workspace/.htests'
const WORKSPACE = process.env.WORKSPACE_DIR || '/workspace'

export default defineConfig({
  cacheDir: path.join(ROOT, '.vite-project-cache'),
  resolve: { alias: { '@': path.join(WORKSPACE, 'js') } },
  test: {
    root: WORKSPACE,
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'http://localhost:3000/' } },
    setupFiles: [path.join(ROOT, 'setup.mjs')],
    include: ['js/directives.spec.js'],
    testTimeout: 20000,
  },
})
