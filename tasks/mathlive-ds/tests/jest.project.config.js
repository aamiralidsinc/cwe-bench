'use strict';
/**
 * The project's own unit tests for the affected area, restored from /tests before the
 * run so that edits inside the solver's tree cannot weaken them. Snapshot-based markup
 * tests are excluded on purpose: a correct encoding fix legitimately changes the
 * expected HTML strings, and the project's snapshots are not part of the contract here.
 */
const path = require('path');

const rootDir = process.env.WORKSPACE_DIR || '/workspace';
const out = process.env.JUNIT_OUT || path.join(rootDir, '.htests', 'project.xml');

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
  roots: [path.join(rootDir, 'test')],
  testMatch: [
    '**/security.test.ts',
    '**/static-elements.test.ts',
    '**/latex.test.ts',
    '**/math-ascii.test.ts',
  ],
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
