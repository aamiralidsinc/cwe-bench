import { Liquid } from '../../src/liquid'
import {
  sparse, withArrayPrototype, withObjectPrototype,
  ARRAY_MARKERS, FIRST_MARKER, SIZE_MARKER
} from '../support/prototype'

describe('turning the read restriction off keeps prototype lookup', function () {
  it('the engine option', function () {
    const engine = new Liquid({ ownPropertyOnly: false })
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync(
      '{{ a[-1] }}|{{ a.first }}|{{ a.last }}|{{ a | first }}|{{ a | last }}', { a }))
    expect(out).toBe(`${ARRAY_MARKERS[2]}|${ARRAY_MARKERS[0]}|${ARRAY_MARKERS[2]}|${ARRAY_MARKERS[0]}|${ARRAY_MARKERS[2]}`)
  })

  it('the render option overrides the engine default', function () {
    const engine = new Liquid()
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync(
      '{{ a[-1] }}', { a }, { ownPropertyOnly: false }))
    expect(out).toBe(ARRAY_MARKERS[1])
  })

  it('the render option can turn the restriction back on', function () {
    const engine = new Liquid({ ownPropertyOnly: false })
    const out = withObjectPrototype(() => engine.parseAndRenderSync(
      '{{ o.secret }}', { o: {} }, { ownPropertyOnly: true }))
    expect(out).toBe('')
  })

  it('inherited end names and sizes stay visible', function () {
    const engine = new Liquid({ ownPropertyOnly: false })
    const out = withObjectPrototype(() => {
      const first = engine.parseAndRenderSync('{{ o.first }}', { o: {} })
      const size = engine.parseAndRenderSync('{{ a.size }}', { a: sparse(4) })
      return { first, size }
    })
    expect(out.first).toBe(FIRST_MARKER)
    expect(out.size).toBe(SIZE_MARKER)
  })
})
