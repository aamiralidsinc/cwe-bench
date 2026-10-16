// Shared vitest configuration for the CWE verifier. The code under test is the
// solver's source under /app, reached through the "@ss" alias. Test files live
// beside this config (copied to a writable dir by test.sh, since vite writes a
// temp file next to the config). All tests share one on-disk SQLite account
// database, so they must run serially (single fork, no file parallelism).
export function baseConfig(dir, group, outputFile) {
  return {
    root: '/app/packages/sync-server',
    resolve: {
      alias: { '@ss': '/app/packages/sync-server/src' },
    },
    server: {
      fs: { allow: ['/'], strict: false },
    },
    test: {
      globals: true,
      environment: 'node',
      include: [`${dir}/${group}/**/*.test.js`],
      globalSetup: [`${dir}/lib/global-setup.js`],
      fileParallelism: false,
      maxWorkers: 1,
      minWorkers: 1,
      hookTimeout: 30000,
      testTimeout: 30000,
      reporters: ['default', ['junit', { outputFile }]],
      outputFile: { junit: outputFile },
    },
  };
}
