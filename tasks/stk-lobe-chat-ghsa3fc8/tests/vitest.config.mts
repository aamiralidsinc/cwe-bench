import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

// Runtime location: /workspace/.htests/vitest.config.mts (staged there by test.sh).
const workspace = fileURLToPath(new URL('..', import.meta.url));

export default defineConfig({
  cacheDir: fileURLToPath(new URL('.vite-cache', import.meta.url)),
  root: workspace,
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('../src', import.meta.url)),
    },
  },
  test: {
    environment: 'node',
    fileParallelism: false,
    globals: true,
    hookTimeout: 60_000,
    include: ['.htests/**/*.test.ts'],
    pool: 'forks',
    poolOptions: { forks: { singleFork: true } },
    testTimeout: 60_000,
  },
});
