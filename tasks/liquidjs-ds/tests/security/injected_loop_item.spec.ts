import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('loop metadata does not expose a prototype value', function () {
  const engine = new Liquid({ templates: { item: '[{{ forloop.item }}]' } })

  it('a loop over the sequence', function () {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{% for x in a %}[{{ forloop.item }}]{% endfor %}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })

  it('a partial rendered for the sequence', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{% render "item" for a as x %}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })

  it('a table row over the sequence', function () {
    const a = sparse(2)
    const out = withArrayPrototype(() => engine.parseAndRenderSync('{% tablerow x in a %}[{{ tablerowloop.item }}]{% endtablerow %}', { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })
})
