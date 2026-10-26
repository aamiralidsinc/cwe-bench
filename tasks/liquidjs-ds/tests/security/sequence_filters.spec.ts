import { Liquid } from '../../src/liquid'
import { sparse, withArrayPrototype, ARRAY_MARKERS, expectNoMarkers } from '../support/prototype'

describe('sequence filters expose no prototype value', function () {
  const engine = new Liquid()

  const cases: [string, (a: any[]) => string][] = [
    ['join', (a) => engine.parseAndRenderSync('{{ a | join: "," }}', { a })],
    ['compact', (a) => engine.parseAndRenderSync('{{ a | compact | join: "," }}', { a })],
    ['concat', (a) => engine.parseAndRenderSync('{{ a | concat: b | join: "," }}', { a, b: sparse(1) })],
    ['slice', (a) => engine.parseAndRenderSync('{{ a | slice: 0, 2 | join: "," }}', { a })],
    ['sort', (a) => engine.parseAndRenderSync('{{ a | sort | join: "," }}', { a })],
    ['reverse', (a) => engine.parseAndRenderSync('{{ a | reverse | join: "," }}', { a })]
  ]

  it.each(cases)('%s', function (_name, render) {
    const a = sparse(3)
    const out = withArrayPrototype(() => render(a))
    expectNoMarkers(out, ARRAY_MARKERS)
  })

  it('a filter result that is assigned and indexed later carries no prototype value', function () {
    const a = sparse(2)
    const src = '{% assign b = a | compact %}[{{ b[0] }}][{{ b }}]'
    const out = withArrayPrototype(() => engine.parseAndRenderSync(src, { a }))
    expectNoMarkers(out, ARRAY_MARKERS)
  })
})
