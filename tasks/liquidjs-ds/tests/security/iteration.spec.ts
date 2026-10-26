import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('iteration over a sequence exposes no prototype value', function () {
  const engine = new Liquid({ templates: { item: '[{{ x }}]' } })

  const cases: [string, string][] = [
    ['a plain loop', '{% for x in a %}[{{ x }}]{% endfor %}'],
    ['a loop with reversed', '{% for x in a reversed %}[{{ x }}]{% endfor %}'],
    ['a loop with limit', '{% for x in a limit: 2 %}[{{ x }}]{% endfor %}'],
    ['a loop with offset', '{% for x in a offset: 1 %}[{{ x }}]{% endfor %}'],
    ['a table row', '{% tablerow x in a cols: 2 %}[{{ x }}]{% endtablerow %}'],
    ['a partial rendered for the sequence', '{% render "item" for a as x %}']
  ]

  it.each(cases)('%s', function (_name, src) {
    const a = sparse(3)
    const out = withArrayPrototype(() => engine.parseAndRenderSync(src, { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
    expect(out).not.toContain('__LQ')
  })
})
