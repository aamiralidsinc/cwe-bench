'use strict';

// Runs the project's own spec against the submitted sources. The spec is staged next to this
// file at /workspace/.htests, so its `../index` import resolves to /workspace/index.ts.
module.exports = {
  rootDir: __dirname,
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['<rootDir>/index.spec.ts'],
  cacheDirectory: '/tmp/jest-cache',
  globals: {
    'ts-jest': {
      diagnostics: false,
      tsconfig: {
        target: 'es6',
        moduleResolution: 'bundler',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
        resolveJsonModule: true,
        skipLibCheck: true,
        types: ['jest'],
      },
    },
  },
};
