import { Liquid } from '../../src/liquid'
import {
  sparse, withArrayPrototype, withObjectPrototype,
  ARRAY_MARKERS, FIRST_MARKER, LAST_MARKER, expectNoMarkers
} from '../support/prototype'

describe('end-of-sequence named reads expose no prototype value', function () {
  const engine = new Liquid()

  it('renders nothing for a first slot that is not an own element', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a.first }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('renders nothing for a last slot that is not an own element', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a.last }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('renders nothing when a plain object inherits those names', function () {
    const out = withObjectPrototype(() => engine.parseAndRenderSync('{{ o.first }}|{{ o.last }}', { o: {} }))
    expectNoMarkers(out, [FIRST_MARKER, LAST_MARKER])
    expect(out).toBe('|')
  })

  it('the programmatic evaluation returns no value for an inherited end name', function () {
    const out = withObjectPrototype(() => engine.evalValueSync('o.first', { o: {} }))
    expectNoMarkers(out, [FIRST_MARKER])
    expect(out === undefined || out === null || out === '').toBe(true)
  })
})
