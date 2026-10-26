import { Liquid } from '../../src/liquid'

describe('iteration over ordinary sequences keeps working', function () {
  const engine = new Liquid({ templates: { item: '[{{ x }}:{{ forloop.item }}]' } })
  const arr = ['a', 'b', 'c']

  it('a plain loop', function () {
    expect(engine.parseAndRenderSync('{% for x in arr %}[{{ x }}]{% endfor %}', { arr })).toBe('[a][b][c]')
  })

  it('loop modifiers', function () {
    expect(engine.parseAndRenderSync('{% for x in arr reversed %}[{{ x }}]{% endfor %}', { arr })).toBe('[c][b][a]')
    expect(engine.parseAndRenderSync('{% for x in arr limit: 2 %}[{{ x }}]{% endfor %}', { arr })).toBe('[a][b]')
    expect(engine.parseAndRenderSync('{% for x in arr offset: 1 %}[{{ x }}]{% endfor %}', { arr })).toBe('[b][c]')
  })

  it('the loop item name', function () {
    expect(engine.parseAndRenderSync('{% for x in arr %}[{{ forloop.item }}]{% endfor %}', { arr })).toBe('[a][b][c]')
  })

  it('a table row', function () {
    const out = engine.parseAndRenderSync('{% tablerow x in arr cols: 2 %}{{ x }}{% endtablerow %}', { arr })
    expect(out).toBe('<tr class="row1"><td class="col1">a</td><td class="col2">b</td></tr>' +
      '<tr class="row2"><td class="col1">c</td></tr>')
  })

  it('a partial rendered for the sequence', function () {
    expect(engine.parseAndRenderSync('{% render "item" for arr as x %}', { arr })).toBe('[a:a][b:b][c:c]')
  })
})
