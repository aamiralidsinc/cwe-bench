const path = require('path');

// The verifier restores the submission at /workspace and stages this directory at
// /workspace/.htests/support, so the workspace root is two levels up.
const workspace = path.resolve(__dirname, '..', '..');

module.exports = {
  rootDir: workspace,
  testEnvironment: 'node',
  testMatch: ['<rootDir>/.htests/**/*.test.ts', '<rootDir>/nodes/**/__tests__/**/*.test.ts'],
  transform: {
    '^.+\\.tsx?$': [
      'ts-jest',
      {
        tsconfig: path.join(__dirname, 'tsconfig.test.json'),
        diagnostics: true,
      },
    ],
  },
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  moduleNameMapper: {
    '^better-sqlite3$': path.join(__dirname, 'fake-better-sqlite3.js'),
  },
  cacheDirectory: '/tmp/sqlite-path-guard-jest-cache',
};
