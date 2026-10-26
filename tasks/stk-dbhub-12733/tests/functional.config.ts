import path from 'path';

const ROOT = process.env.APP_ROOT || '/workspace';
const HERE = path.join(ROOT, '.htests');

export default {
  cacheDir: path.join(HERE, '.vite-cache'),
  server: { fs: { allow: [ROOT, '/opt', '/tmp'] } },
  test: {
    globals: true,
    environment: 'node',
    root: ROOT,
    include: [
      '.htests/functional/**/*.test.ts',
      'src/utils/__tests__/allowed-keywords.test.ts',
      'src/utils/__tests__/sql-parser.test.ts',
      'src/tools/__tests__/execute-sql.test.ts',
    ],
    testTimeout: 60000,
    hookTimeout: 60000,
    isolate: true,
    fileParallelism: false,
    pool: 'forks',
    poolOptions: { forks: { singleFork: true } },
    reporters: ['default', ['junit', { outputFile: process.env.JUNIT_OUT || path.join(HERE, 'functional-results.xml') }]],
  },
};
