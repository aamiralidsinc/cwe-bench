import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('the window lookup exposes no prototype value', function () {
  const engine = new Liquid()

  it('the window itself', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('[{{ a | take: 2 }}]', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('[]')
  })

  it('the window combined with joining', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('[{{ a | take: 2 | join: "," }}]', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })
})
