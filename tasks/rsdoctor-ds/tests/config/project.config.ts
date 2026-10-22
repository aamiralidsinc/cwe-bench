import { defineConfig } from '@rstest/core';

process.env.NO_COLOR = '1';

export default defineConfig({
  name: 'project',
  root: '/workspace',
  globals: true,
  restoreMocks: true,
  pool: { maxWorkers: 1 },
  source: {
    decorators: { version: 'legacy' },
    tsconfigPath: './tsconfig.test.json',
  },
  include: [
    'packages/sdk/tests/server/**/*.test.ts',
    'packages/utils/tests/server.test.ts',
    'packages/core/tests/build/utils/config.test.ts',
  ],
  setupFiles: ['./scripts/rstest.setup.ts'],
  reporters: [
    ['junit', { outputPath: process.env.RSD_JUNIT_PROJECT_OUT ?? '/logs/verifier/functional/project.xml' }],
  ],
});
