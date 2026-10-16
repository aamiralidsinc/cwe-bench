// Hidden-test runner config. The library under test is the source tree in /app
// (APP_DIR overrides it for local runs); tests import it as 'class-transformer'.
const path = require('path');
const app = process.env.APP_DIR || '/app';

module.exports = {
  rootDir: __dirname,
  testEnvironment: 'node',
  testMatch: ['**/*.spec.ts'],
  transform: { '^.+\\.ts$': path.join(app, 'node_modules', 'ts-jest') },
  moduleNameMapper: { '^class-transformer$': path.join(app, 'src', 'index.ts') },
  modulePaths: [path.join(app, 'node_modules')],
  globals: { 'ts-jest': { tsconfig: path.join(__dirname, 'tsconfig.json'), isolatedModules: true } },
};
