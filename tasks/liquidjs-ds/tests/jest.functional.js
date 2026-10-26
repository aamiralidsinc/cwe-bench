// Hidden functional suite plus pristine copies of the project's own tests for the areas this
// task touches. The project copies are restored from the verifier image's pristine checkout,
// so the agent's edits to them cannot affect grading.
const path = require('path')
const root = path.resolve(__dirname, '..')
const junit = process.env.JUNIT_PATH

module.exports = {
  rootDir: root,
  testEnvironment: 'node',
  testMatch: [
    '<rootDir>/.htests/functional/**/*.spec.ts',
    '<rootDir>/src/context/context.spec.ts',
    '<rootDir>/test/integration/filters/array.spec.ts',
    '<rootDir>/test/integration/tags/for.spec.ts',
    '<rootDir>/test/integration/tags/tablerow.spec.ts',
    '<rootDir>/test/integration/tags/render.spec.ts',
    '<rootDir>/test/integration/liquid/keepoutput-opt.spec.ts'
  ],
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  transform: {
    '^.+\\.ts$': ['ts-jest', { tsconfig: path.join(__dirname, 'tsconfig.json') }]
  },
  reporters: junit ? ['default', [junit, {}]] : ['default'],
  testTimeout: 30000
}
