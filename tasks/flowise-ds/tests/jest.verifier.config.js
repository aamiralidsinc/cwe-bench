// Verifier jest config. Runs the hidden specs against the product source tree
// (PRODUCT_ROOT, default /app/packages/server/src) with all infrastructure
// dependencies stubbed, so no network, database, or project build is needed.
const path = require('path')

const HERE = __dirname
const PRODUCT_ROOT = process.env.PRODUCT_ROOT || '/app/packages/server/src'
const GROUP = process.env.VERIFIER_GROUP || 'security'
const NM = process.env.VERIFIER_NODE_MODULES
const mod = (name) => (NM ? path.join(NM, name) : name)

module.exports = {
    rootDir: HERE,
    // roots are the trees jest crawls AND transforms: our tests/support plus the
    // product source. Test discovery is narrowed to the current group via testMatch.
    roots: [HERE, PRODUCT_ROOT],
    modulePaths: NM ? [NM] : [],
    testMatch: [path.join(HERE, GROUP, '**/*.spec.ts')],
    testEnvironment: 'node',
    transformIgnorePatterns: [],
    transform: {
        '^.+\\.tsx?$': [mod('babel-jest'), { configFile: path.join(HERE, 'babel.verifier.config.js') }]
    },
    // Redirects product infrastructure modules by their resolved absolute path, so
    // a fix that introduces new helper files still reaches the stubs.
    resolver: path.join(HERE, 'support', 'resolver.js'),
    moduleNameMapper: {
        '^@product/(.*)$': path.join(PRODUCT_ROOT, '$1')
    },
    reporters: [
        'default',
        [
            mod('jest-junit'),
            {
                outputDirectory: process.env.JEST_JUNIT_OUTPUT_DIR || path.join('/logs/verifier', GROUP),
                outputName: 'results.xml'
            }
        ]
    ],
    verbose: true,
    testTimeout: 30000
}
