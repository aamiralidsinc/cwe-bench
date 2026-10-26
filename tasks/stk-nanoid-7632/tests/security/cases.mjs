/*
 * Hidden security cases. Every case drives a public entry point of the product and states its
 * expected result as a literal: an ID whose requested length cannot be produced must come back as
 * the empty string, and the call must come back at all. A case that does not return inside the
 * runner's timeout is a failure (that is the reported denial of service).
 */

const ZEROS = 'zeros'

export const cases = [
  // --- the custom generator closure reached through the Node entry point ---
  {
    id: 'T1-node-default-zero',
    name: 'a custom generator created with a zero default returns immediately',
    module: 'index.js',
    expr: "m.customAlphabet('0123456789', 0)()",
    expect: { kind: 'empty' }
  },
  {
    id: 'T1-node-call-zero',
    name: 'a zero size passed to an otherwise valid generator yields an empty ID',
    module: 'index.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(0)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T1-node-call-negative',
    name: 'a negative size passed to an otherwise valid generator yields an empty ID',
    module: 'index.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(-3)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T1-node-default-negative',
    name: 'a custom generator created with a negative default yields an empty ID',
    module: 'index.js',
    expr: `m.customRandom('ab', -5, ${ZEROS})()`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T5-node-call-nan',
    name: 'a non-numeric size value that is not a number yields an empty ID',
    module: 'index.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(NaN)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T5-node-call-infinity',
    name: 'an unbounded numeric size yields an empty ID',
    module: 'index.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(Infinity)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T5-node-call-text',
    name: 'a size supplied as non-numeric text yields an empty ID',
    module: 'index.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})('abc')`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T9-cli-size-overflow',
    name: 'the command-line tool returns instead of spinning on an unbounded size value',
    kind: 'cli',
    args: ['--alphabet', 'abc', '--size', '1e999'],
    expect: { kind: 'cli-blocked' }
  },

  // --- the same decision in the bundler / react-native implementation ---
  {
    id: 'T2-browser-default-zero',
    name: 'the bundler build returns an empty ID for a zero default',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 0, ${ZEROS})()`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T2-browser-call-zero',
    name: 'the bundler build returns an empty ID for a zero size',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(0)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T2-browser-call-negative',
    name: 'the bundler build returns an empty ID for a negative size',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(-3)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T2-browser-default-negative',
    name: 'the bundler build returns an empty ID for a negative default',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', -1, ${ZEROS})()`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T10-browser-call-nan',
    name: 'the bundler build returns an empty ID for a non-numeric size',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(NaN)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T10-browser-call-infinity',
    name: 'the bundler build returns an empty ID for an unbounded size',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(Infinity)`,
    expect: { kind: 'empty' }
  },
  {
    id: 'T10-browser-call-text',
    name: 'the bundler build returns an empty ID for a text size',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})('abc')`,
    expect: { kind: 'empty' }
  },

  // --- the documented non-secure implementation ---
  {
    id: 'T3-nonsecure-default-negative',
    name: 'the non-secure generator returns for a negative default',
    module: 'non-secure/index.js',
    expr: "m.customAlphabet('abc', -1)()",
    expect: { kind: 'empty' }
  },
  {
    id: 'T3-nonsecure-call-negative',
    name: 'the non-secure generator returns for a negative call size',
    module: 'non-secure/index.js',
    expr: "m.customAlphabet('abc', 5)(-3)",
    expect: { kind: 'empty' }
  },
  {
    id: 'T4-nonsecure-nanoid-negative',
    name: 'the plain non-secure ID call returns for a negative size',
    module: 'non-secure/index.js',
    expr: "m.nanoid(-1)",
    expect: { kind: 'empty' }
  },
  {
    id: 'T4-nonsecure-nanoid-negative-text',
    name: 'the plain non-secure ID call returns for a negative size given as text',
    module: 'non-secure/index.js',
    expr: "m.nanoid('-2')",
    expect: { kind: 'empty' }
  },

  // --- progress that does not depend on the size the caller passes ---
  {
    id: 'T7-node-factory-zero-default',
    name: 'a generator whose creation-time size makes no progress returns for a valid call size',
    module: 'index.js',
    expr: `m.customRandom('abc', 0, ${ZEROS})(5)`,
    expect: { kind: 'lengthIn', values: [0, 5] }
  },
  {
    id: 'T6-node-empty-alphabet',
    name: 'a custom generator with no symbols returns instead of spinning',
    module: 'index.js',
    expr: "m.customAlphabet('', 5)()",
    expect: { kind: 'empty' }
  },
  {
    id: 'T7-browser-factory-negative-default',
    name: 'the bundler build returns when its creation-time size makes no progress',
    module: 'index.browser.js',
    expr: `m.customRandom('abc', -1, ${ZEROS})(4)`,
    expect: { kind: 'lengthIn', values: [0, 4] }
  },
  {
    id: 'T6-browser-empty-alphabet',
    name: 'the bundler build returns when the generator has no symbols',
    module: 'index.browser.js',
    expr: "m.customAlphabet('', 5)()",
    expect: { kind: 'empty' }
  }
]
