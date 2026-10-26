import path from 'path';

const ROOT = process.env.APP_ROOT || '/workspace';
const HERE = path.join(ROOT, '.htests');

export default {
  cacheDir: path.join(HERE, '.vite-cache'),
  server: { fs: { allow: [ROOT, '/opt/test-tools', '/tmp'] } },
  test: {
    globals: true,
    environment: 'jsdom',
    root: ROOT,
    include: [
      '.htests/functional/**/*.test.ts',
      'library/src/methods/flatten/flatten.test.ts',
      'library/src/methods/summarize/summarize.test.ts',
      'library/src/schemas/intersect/intersect.test.ts',
      'library/src/schemas/intersect/utils/_merge/_merge.test.ts',
      'library/src/schemas/strictObject/strictObject.test.ts',
      'library/src/schemas/objectWithRest/objectWithRest.test.ts',
      'library/src/schemas/looseObject/looseObject.test.ts',
      'library/src/schemas/record/record.test.ts',
      'library/src/schemas/map/map.test.ts',
      'library/src/utils/getDotPath/getDotPath.test.ts',
    ],
    testTimeout: 60000,
    hookTimeout: 60000,
    fileParallelism: false,
    pool: 'forks',
    poolOptions: { forks: { singleFork: true } },
    reporters: [
      'default',
      [
        'junit',
        {
          outputFile:
            process.env.JUNIT_OUT || path.join(HERE, 'functional-results.xml'),
        },
      ],
    ],
  },
};
