'use strict';
/**
 * Hidden security and functional suites. They live in /workspace/.htests at grading
 * time and import the solver's product sources, so any implementation of the rule is
 * exercised. Offline and deterministic.
 */
const path = require('path');

const rootDir = process.env.WORKSPACE_DIR || '/workspace';
const out = process.env.JUNIT_OUT || path.join(rootDir, '.htests', 'results.xml');

const tsJest = [
  'ts-jest',
  {
    useESM: false,
    isolatedModules: true,
    tsconfig: {
      allowJs: true,
      module: 'commonjs',
      moduleResolution: 'node',
      target: 'es2020',
      esModuleInterop: true,
      resolveJsonModule: true,
      jsx: 'react',
      baseUrl: path.join(rootDir, 'src'),
    },
  },
];

module.exports = {
  rootDir,
  roots: [path.join(rootDir, '.htests')],
  testMatch: ['**/security/**/*.test.ts', '**/functional/**/*.test.ts'],
  testEnvironment: 'node',
  moduleDirectories: ['node_modules', path.join(rootDir, 'src')],
  moduleNameMapper: {
    '.*\\.(sass|less|css)$': path.join(rootDir, '.htests/support/styleMock.js'),
  },
  moduleFileExtensions: ['js', 'json', 'ts', 'esm.js'],
  transform: {
    '^.+\\.js$': tsJest,
    '^.+\\.tsx?$': tsJest,
  },
  testTimeout: 30000,
  reporters: [
    'default',
    [path.join(rootDir, '.htests/support/junit-reporter.js'), { outputFile: out }],
  ],
};
