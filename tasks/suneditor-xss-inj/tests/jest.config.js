// Hidden-test runner config. The plugin under test is the source in /app (APP_DIR overrides
// it for local runs). Tests reach it through the '@product' alias and mock the editor's
// helper/contract modules (aliased) so the real plugin runs against a jsdom document.
const path = require('path');
const app = process.env.APP_DIR || '/app';
module.exports = {
  rootDir: __dirname,
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: [path.join(app, 'test', 'setup.js')],
  transform: {
    '^.+\\.js$': [path.join(app, 'node_modules', 'babel-jest'), {
      presets: [[path.join(app, 'node_modules', '@babel', 'preset-env'), { targets: { node: 'current' } }]],
      plugins: [path.join(app, 'node_modules', '@babel', 'plugin-transform-class-properties'), path.join(app, 'node_modules', '@babel', 'plugin-transform-private-methods')],
    }],
  },
  moduleNameMapper: {
    '^@product$': path.join(app, 'src', 'plugins', 'modal', 'embed.js'),
    '^@helper$': path.join(app, 'src', 'helper', 'index.js'),
    '^@contract$': path.join(app, 'src', 'modules', 'contract', 'index.js'),
    '^@editorMock$': path.join(app, 'test', '__mocks__', 'editorMock.js'),
  },
  modulePaths: [path.join(app, 'node_modules')],
  reporters: ['default', ['/opt/junit/node_modules/jest-junit', {}]],
  forceExit: true,
};
