import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('printing a sequence exposes no prototype value', function () {
  const engine = new Liquid()

  it('direct output', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('[{{ a }}]', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('[]')
  })

  it('json', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | json }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })

  it('inspect', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | inspect }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })

  it('sentence output', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a | array_to_sentence_string }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })
})
