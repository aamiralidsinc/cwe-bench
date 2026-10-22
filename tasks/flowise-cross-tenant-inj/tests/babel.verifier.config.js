// Babel config used by babel-jest to transform the product TypeScript (and the
// test/stub TypeScript) for the verifier. Types are stripped; decorators on
// entity classes are parsed with the legacy proposal so they can be no-ops.
const NM = process.env.VERIFIER_NODE_MODULES
const mod = (name) => (NM ? require(require('path').join(NM, name)) : require(name))

module.exports = {
    presets: [
        [mod('@babel/preset-env'), { targets: { node: 'current' } }],
        [mod('@babel/preset-typescript'), {}]
    ],
    plugins: [
        [mod('@babel/plugin-proposal-decorators'), { legacy: true }],
        [mod('@babel/plugin-transform-class-properties'), { loose: true }]
    ]
}
