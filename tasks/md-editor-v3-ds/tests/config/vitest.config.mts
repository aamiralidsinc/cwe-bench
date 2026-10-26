import { defineConfig } from 'vitest/config';
import vueJsx from '@vitejs/plugin-vue-jsx';
import os from 'node:os';
import path from 'node:path';

// The product tree the submission was restored into. The hidden suites import the public
// preview entry and the public configuration module through the project's own path aliases.
const ROOT = process.env.MD_ROOT || '/workspace';

export default defineConfig({
  root: ROOT,
  cacheDir: path.join(os.tmpdir(), 'md-editor-vitest-cache'),
  plugins: [vueJsx()],
  resolve: {
    alias: [
      { find: '~~', replacement: path.join(ROOT, 'packages') },
      { find: '~', replacement: path.join(ROOT, 'packages/MdEditor') }
    ],
    dedupe: ['vue']
  },
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false
  },
  test: {
    environment: 'jsdom',
    environmentOptions: { jsdom: { runScripts: 'dangerously' } },
    globals: false,
    include: ['.htests/**/*.test.ts'],
    exclude: ['**/node_modules/**'],
    testTimeout: 30000,
    hookTimeout: 30000,
    fileParallelism: false
  }
});
