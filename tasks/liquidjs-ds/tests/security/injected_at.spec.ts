import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('the positional lookup exposes no prototype value', function () {
  const engine = new Liquid()

  it('a positive position', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | at: 1 }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('a position counted from the end', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | at: -1 }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })
})
