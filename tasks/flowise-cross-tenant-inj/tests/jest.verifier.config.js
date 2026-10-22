// Verifier jest config. Runs the hidden specs against the product source tree
// (PRODUCT_ROOT, default /app/packages/server/src) with all infrastructure
// dependencies stubbed, so no network, database, or project build is needed.
const path = require('path')

const HERE = __dirname
const PRODUCT_ROOT = process.env.PRODUCT_ROOT || '/app/packages/server/src'
const GROUP = process.env.VERIFIER_GROUP || 'security'
const stub = (name) => path.join(HERE, 'support', 'stubs', name)
const NM = process.env.VERIFIER_NODE_MODULES
const mod = (name) => (NM ? path.join(NM, name) : name)

module.exports = {
    rootDir: HERE,
    // roots are the trees jest crawls AND transforms: our tests/support plus the
    // product source. Test discovery is narrowed to the current group via testMatch.
    roots: [HERE, PRODUCT_ROOT],
    modulePaths: process.env.VERIFIER_NODE_MODULES ? [process.env.VERIFIER_NODE_MODULES] : [],
    testMatch: [path.join(HERE, GROUP, '**/*.spec.ts')],
    testEnvironment: 'node',
    // Any spelling that resolves to the product's utils modules is mapped to
    // the offline stubs (moduleNameMapper above handles the common spellings).
    resolver: path.join(HERE, 'support', 'resolver.js'),
    transformIgnorePatterns: [],
    transform: {
        '^.+\\.tsx?$': [
            mod('babel-jest'),
            { configFile: path.join(HERE, 'babel.verifier.config.js') }
        ]
    },
    // First match wins. Specific infra paths before the generic utils barrel.
    moduleNameMapper: {
        '^openai$': stub('openai.js'),
        '^flowise-components$': stub('flowise-components.js'),
        '^express$': stub('express.js'),
        '^typeorm$': stub('typeorm.js'),
        '^content-disposition$': stub('content-disposition.js'),
        '^\\.\\./\\.\\./utils/getRunningExpressApp$': stub('getRunningExpressApp.js'),
        '^\\.\\./\\.\\./utils/fileValidation$': stub('fileValidation.js'),
        '^\\.\\./\\.\\./utils$': stub('utils.js'),
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
