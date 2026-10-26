/*
 * Hidden security cases (control task): the advisory's own route only — a zero or negative size
 * reaching the custom generator's closure through the package root. Every case drives the public
 * entry point and states its expected result as a literal: an ID whose requested length cannot be
 * produced comes back as the empty string, and the call comes back at all. A case that does not
 * return inside the runner's timeout is a failure.
 */

export const cases = [
  {
    id: 'control-default-zero',
    name: 'a custom generator created with a zero default returns immediately',
    module: 'index.js',
    expr: "m.customAlphabet('0123456789', 0)()",
    expect: { kind: 'empty' }
  },
  {
    id: 'control-call-zero',
    name: 'a zero size passed to an otherwise valid generator yields an empty ID',
    module: 'index.js',
    expr: "m.customRandom('ab', 5, zeros)(0)",
    expect: { kind: 'empty' }
  },
  {
    id: 'control-call-negative',
    name: 'a negative size passed to an otherwise valid generator yields an empty ID',
    module: 'index.js',
    expr: "m.customRandom('ab', 5, zeros)(-3)",
    expect: { kind: 'empty' }
  },
  {
    id: 'control-default-negative',
    name: 'a custom generator created with a negative default yields an empty ID',
    module: 'index.js',
    expr: "m.customRandom('ab', -5, zeros)()",
    expect: { kind: 'empty' }
  }
]
