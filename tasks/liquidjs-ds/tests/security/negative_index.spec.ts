import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('negative index reads expose no prototype value', function () {
  const engine = new Liquid()

  it('renders nothing when the last slot is not an own element', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a[-1] }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('renders nothing for other negative offsets', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{{ a[-2] }}|{{ a[-3] }}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })

  it('renders nothing when the index comes from a template variable', function () {
    const a = sparse(2)
    const src = '{% assign i = -1 %}{{ a[i] }}'
    const out = withArrayPrototype(() => engine.parseAndRenderSync(src, { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).toBe('')
  })

  it('the programmatic evaluation returns no value for a negative index', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.evalValueSync('a[-1]', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out === undefined || out === null || out === '').toBe(true)
  })
})
