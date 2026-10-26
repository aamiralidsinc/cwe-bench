// Hidden security suite. Lives at /workspace/.htests/jest.security.js in the verifier so the
// unprivileged runner can read it; the product sources are the agent's, at /workspace/src.
const path = require('path')
const root = path.resolve(__dirname, '..')
const junit = process.env.JUNIT_PATH

module.exports = {
  rootDir: root,
  testEnvironment: 'node',
  testMatch: ['<rootDir>/.htests/security/**/*.spec.ts'],
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  transform: {
    '^.+\\.ts$': ['ts-jest', { tsconfig: path.join(__dirname, 'tsconfig.json') }]
  },
  reporters: junit ? ['default', [junit, {}]] : ['default'],
  testTimeout: 30000
}
