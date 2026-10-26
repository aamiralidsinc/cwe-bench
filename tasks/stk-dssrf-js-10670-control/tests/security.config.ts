import path from 'path';

const ROOT = process.env.APP_ROOT || '/workspace';
const HERE = path.join(ROOT, '.htests');

export default {
  cacheDir: path.join(HERE, '.vite-cache'),
  server: { fs: { allow: [ROOT, '/opt/test-tools', '/tmp'] } },
  test: {
    globals: true,
    environment: 'node',
    root: ROOT,
    include: ['.htests/security/**/*.test.ts'],
    testTimeout: 120000,
    hookTimeout: 60000,
    fileParallelism: false,
    pool: 'forks',
    reporters: [
      'default',
      [
        'junit',
        {
          outputFile:
            process.env.JUNIT_OUT || path.join(HERE, 'security-results.xml'),
        },
      ],
    ],
  },
};
