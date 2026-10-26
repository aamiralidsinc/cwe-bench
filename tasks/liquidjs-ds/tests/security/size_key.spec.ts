import { Liquid } from '../../src/liquid'
import { sparse, withObjectPrototype, SIZE_MARKER, expectNoMarkers } from '../support/prototype'

describe('the reported size exposes no prototype value', function () {
  const engine = new Liquid()

  it('a sequence reports its length, not an inherited size', function () {
    const a = sparse(3)
    const out = withObjectPrototype(() => engine.parseAndRenderSync('{{ a.size }}', { a }))
    expectNoMarkers(out, [SIZE_MARKER])
    expect(out).toBe('3')
  })

  it('a plain object reports its own key count, not an inherited size', function () {
    const o = { one: 1, two: 2 }
    const out = withObjectPrototype(() => engine.parseAndRenderSync('{{ o.size }}', { o }))
    expectNoMarkers(out, [SIZE_MARKER])
    expect(out).toBe('2')
  })

  it('a string reports its length, not an inherited size', function () {
    const out = withObjectPrototype(() => engine.parseAndRenderSync('{{ s.size }}', { s: 'abc' }))
    expectNoMarkers(out, [SIZE_MARKER])
    expect(out).toBe('3')
  })

  it('the programmatic evaluation reports the structural size', function () {
    const a = sparse(4)
    const out = withObjectPrototype(() => engine.evalValueSync('a.size', { a }))
    expectNoMarkers(out, [SIZE_MARKER])
    expect(out).toBe(4)
  })
})
