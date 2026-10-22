import { defineConfig } from '@rstest/core';

export default defineConfig({
  name: 'functional',
  root: '/workspace/.htests',
  globals: false,
  include: ['functional/**/*.test.ts'],
  testTimeout: 60000,
  pool: { maxWorkers: 1 },
  reporters: [
    ['junit', { outputPath: process.env.RSD_JUNIT_OUT ?? '/logs/verifier/functional/behaviour.xml' }],
  ],
});
