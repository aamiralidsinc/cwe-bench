/*
 * Hidden functional cases: legitimate use that must keep working, including the values coupled to
 * every hidden route. Every expectation is what the pinned library already produces today; the
 * expected values are literals, never computed with the product.
 */

const ZEROS = 'zeros'
const FAKE = `(() => {
  const sequence = [2, 255, 3, 7, 7, 7, 7, 7, 0, 1]
  function fakeRandom(size) {
    let bytes = []
    for (let i = 0; i < size; i += sequence.length) {
      bytes = bytes.concat(sequence.slice(0, size - i))
    }
    return bytes
  }
  return fakeRandom
})()`

export const cases = [
  // Node implementation
  {
    id: 'F-node-default-21',
    name: 'an omitted size keeps its default length',
    module: 'index.js',
    expr: "m.customAlphabet('abcdef')()",
    expect: { kind: 'length', value: 21 }
  },
  {
    id: 'F-node-one-symbol',
    name: 'a one-symbol alphabet keeps repeating that symbol',
    module: 'index.js',
    expr: "m.customAlphabet('a', 5)()",
    expect: { kind: 'equals', value: 'aaaaa' }
  },
  {
    id: 'F-node-call-size',
    name: 'a call-time size keeps producing exactly that many symbols',
    module: 'index.js',
    expr: "m.customAlphabet('abc')(10)",
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-node-string-size',
    name: 'a size written as a numeric string keeps working',
    module: 'index.js',
    expr: "m.customAlphabet('abc')('10')",
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-node-fractional-size',
    name: 'a fractional size keeps producing the same length as today',
    module: 'index.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(2.1)`,
    expect: { kind: 'length', value: 3 }
  },
  {
    id: 'F-node-byte-sequence-4',
    name: 'a caller-supplied byte source is consumed exactly as before',
    module: 'index.js',
    expr: `m.customRandom('abcde', 4, ${FAKE})()`,
    expect: { kind: 'equals', value: 'adca' }
  },
  {
    id: 'F-node-byte-sequence-18',
    name: 'a longer caller-supplied byte sequence is consumed exactly as before',
    module: 'index.js',
    expr: `m.customRandom('abcde', 18, ${FAKE})()`,
    expect: { kind: 'equals', value: 'cbadcbadcbadcbadcc' }
  },
  {
    id: 'F-node-nanoid-10',
    name: 'the built-in generator keeps its requested length',
    module: 'index.js',
    expr: 'm.nanoid(10)',
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-node-nanoid-string',
    name: 'the built-in generator keeps accepting a numeric string size',
    module: 'index.js',
    expr: "m.nanoid('10')",
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-node-random-buffer',
    name: 'random bytes keep their requested length',
    module: 'index.js',
    expr: 'm.random(10).length',
    expect: { kind: 'equals', value: 10 }
  },
  {
    id: 'F-node-large-default',
    name: 'a larger positive default keeps producing that many symbols',
    module: 'index.js',
    expr: "m.customAlphabet('ab', 40)()",
    expect: { kind: 'length', value: 40 }
  },

  // Bundler / react-native implementation
  {
    id: 'F-browser-default-21',
    name: 'the bundler build keeps the default length',
    module: 'index.browser.js',
    expr: "m.customAlphabet('abcdef')()",
    expect: { kind: 'length', value: 21 }
  },
  {
    id: 'F-browser-one-symbol',
    name: 'the bundler build keeps repeating a one-symbol alphabet',
    module: 'index.browser.js',
    expr: "m.customAlphabet('a', 5)()",
    expect: { kind: 'equals', value: 'aaaaa' }
  },
  {
    id: 'F-browser-string-size',
    name: 'the bundler build keeps accepting a numeric string size',
    module: 'index.browser.js',
    expr: "m.customAlphabet('abc')('10')",
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-browser-fractional-size',
    name: 'the bundler build keeps its fractional-size length',
    module: 'index.browser.js',
    expr: `m.customRandom('ab', 5, ${ZEROS})(2.1)`,
    expect: { kind: 'length', value: 3 }
  },
  {
    id: 'F-browser-byte-sequence',
    name: 'the bundler build keeps consuming a caller-supplied byte source the same way',
    module: 'index.browser.js',
    expr: `m.customRandom('abcde', 4, ${FAKE})()`,
    expect: { kind: 'equals', value: 'adca' }
  },
  {
    id: 'F-browser-nanoid-10',
    name: 'the bundler build keeps its requested length',
    module: 'index.browser.js',
    expr: 'm.nanoid(10)',
    expect: { kind: 'length', value: 10 }
  },

  // Non-secure implementation
  {
    id: 'F-nonsecure-default-21',
    name: 'the non-secure default length is unchanged',
    module: 'non-secure/index.js',
    expr: 'm.nanoid()',
    expect: { kind: 'length', value: 21 }
  },
  {
    id: 'F-nonsecure-size-10',
    name: 'the non-secure requested length is unchanged',
    module: 'non-secure/index.js',
    expr: 'm.nanoid(10)',
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-nonsecure-string-size',
    name: 'the non-secure implementation keeps accepting a numeric string size',
    module: 'non-secure/index.js',
    expr: "m.nanoid('10')",
    expect: { kind: 'length', value: 10 }
  },
  {
    id: 'F-nonsecure-one-symbol',
    name: 'the non-secure implementation keeps repeating a one-symbol alphabet',
    module: 'non-secure/index.js',
    expr: "m.customAlphabet('a', 5)()",
    expect: { kind: 'equals', value: 'aaaaa' }
  },
  {
    id: 'F-nonsecure-call-size',
    name: 'the non-secure call-time size keeps working',
    module: 'non-secure/index.js',
    expr: "m.customAlphabet('abc')(7)",
    expect: { kind: 'length', value: 7 }
  },
  {
    id: 'F-nonsecure-fractional-size',
    name: 'the non-secure fractional-size length is unchanged',
    module: 'non-secure/index.js',
    expr: "m.customAlphabet('abc')(2.1)",
    expect: { kind: 'length', value: 2 }
  },

  // Command-line tool
  {
    id: 'F-cli-default',
    name: 'the command-line tool keeps printing a default-length ID',
    kind: 'cli',
    args: [],
    expect: { kind: 'cli-length', value: 21 }
  },
  {
    id: 'F-cli-size',
    name: 'the command-line tool keeps honouring a requested size',
    kind: 'cli',
    args: ['--size', '10'],
    expect: { kind: 'cli-length', value: 10 }
  },
  {
    id: 'F-cli-alphabet-size',
    name: 'the command-line tool keeps honouring an alphabet and a size',
    kind: 'cli',
    args: ['--alphabet', 'abc', '--size', '15'],
    expect: { kind: 'cli-length', value: 15, charset: 'abc' }
  },
  {
    id: 'F-cli-alphabet-default',
    name: 'the command-line tool keeps the default length when only an alphabet is given',
    kind: 'cli',
    args: ['--alphabet', 'abc'],
    expect: { kind: 'cli-length', value: 21, charset: 'abc' }
  }
]
