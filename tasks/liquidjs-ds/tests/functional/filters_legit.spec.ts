import { Liquid } from '../../src/liquid'

describe('filters over ordinary sequences keep working', function () {
  const engine = new Liquid()
  const arr = ['a', 'b', 'c']
  const other = ['d']

  it('joining and slicing', function () {
    expect(engine.parseAndRenderSync('{{ arr | join: "," }}', { arr })).toBe('a,b,c')
    expect(engine.parseAndRenderSync('{{ arr | slice: 1, 2 }}', { arr })).toBe('bc')
    expect(engine.parseAndRenderSync('{{ arr | take: 2 | join: "," }}', { arr })).toBe('a,b')
    expect(engine.parseAndRenderSync('{{ arr | at: -1 }}', { arr })).toBe('c')
  })

  it('transforming', function () {
    expect(engine.parseAndRenderSync('{{ arr | concat: other | join: "," }}', { arr, other })).toBe('a,b,c,d')
    expect(engine.parseAndRenderSync('{{ arr | reverse | join: "," }}', { arr })).toBe('c,b,a')
    expect(engine.parseAndRenderSync('{{ arr | sort | join: "," }}', { arr: ['c', 'a', 'b'] })).toBe('a,b,c')
    expect(engine.parseAndRenderSync('{{ arr | compact | join: "," }}', { arr })).toBe('a,b,c')
    expect(engine.parseAndRenderSync('{{ arr | uniq | join: "," }}', { arr: ['a', 'a', 'b'] })).toBe('a,b')
  })

  it('serialising', function () {
    expect(engine.parseAndRenderSync('{{ arr | json }}', { arr })).toBe('["a","b","c"]')
    expect(engine.parseAndRenderSync('{{ arr | inspect }}', { arr })).toBe('["a","b","c"]')
    expect(engine.parseAndRenderSync('{{ arr }}', { arr })).toBe('abc')
  })
})
