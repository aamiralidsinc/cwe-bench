import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('end-of-sequence filters expose no prototype value', function () {
  const engine = new Liquid()

  it('renders nothing through the first filter', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | first }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('renders nothing through the last filter', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | last }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('renders nothing when the filter result is assigned before output', function () {
    const a = sparse(2)
    const src = '{% assign x = a | first %}[{{ x }}]{% assign y = a | last %}[{{ y }}]'
    const out = withArrayPrototype(() => engine.parseAndRenderSync(src, { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })
})
