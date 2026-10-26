// Hidden-suite configuration. Test files live beside this config and import product sources through
// the @product alias, which resolves to the restored submission root.
const path = require('path');

const ROOT = process.env.PRODUCT_ROOT || '/workspace';
const HARNESS = process.env.HARNESS_NODE_MODULES || '/opt/harness/node_modules';
const TS_JEST = require.resolve('ts-jest', { paths: [HARNESS] });

const tsconfig = {
  module: 'commonjs',
  target: 'es2022',
  esModuleInterop: true,
  allowJs: true,
  jsx: 'react-jsx',
  experimentalDecorators: true,
  strict: false,
  skipLibCheck: true,
  moduleResolution: 'node',
  resolveJsonModule: true,
  allowSyntheticDefaultImports: true,
};

module.exports = {
  testEnvironment: 'node',
  rootDir: __dirname,
  roots: ['<rootDir>/security', '<rootDir>/functional'],
  testMatch: ['**/*.test.ts'],
  moduleNameMapper: {
    '^@product/(.*)$': ROOT + '/$1',
    '^@novu/shared/utils$': ROOT + '/packages/shared/src/utils/index.ts',
    '^@novu/shared$': ROOT + '/packages/shared/src/index.ts',
    '^@novu/dal$': '<rootDir>/support/novu-dal-stub.js',
    '^@nestjs/swagger$': '<rootDir>/support/nestjs-swagger-stub.js',
    '^@nestjs/common$': '<rootDir>/support/nestjs-common-stub.js',
  },
  modulePaths: [path.join(ROOT, 'node_modules'), HARNESS],
  transform: {
    '^.+\\.tsx?$': [TS_JEST, { diagnostics: false, tsconfig }],
  },
  transformIgnorePatterns: ['/node_modules/(?!(partysocket|mitt)/)'],
  globals: {
    NOVU_API_VERSION: '2024-06-26',
    PACKAGE_NAME: '@novu/js',
    PACKAGE_VERSION: 'test',
  },
  reporters: process.env.JEST_JUNIT_DISABLE === '1' ? ['default'] : [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: process.env.JEST_JUNIT_OUTPUT_DIR || path.join(__dirname, 'junit'),
        outputName: process.env.JEST_JUNIT_OUTPUT_NAME || 'results.xml',
        classNameTemplate: '{filepath}',
        titleTemplate: '{title}',
      },
    ],
  ],
};
