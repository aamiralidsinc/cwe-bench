import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// Staged at /workspace/.htests/vitest.config.mts by the verifier.
const workspace = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig({
  plugins: [vue()],
  cacheDir: fileURLToPath(new URL('.vite-cache', import.meta.url)),
  root: workspace,
  test: {
    environment: 'node',
    fileParallelism: false,
    globals: true,
    include: ['.htests/**/*.test.ts'],
    testTimeout: 60_000,
  },
})
