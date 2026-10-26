import { Liquid } from '../../src/liquid'

describe('string values keep working', function () {
  const engine = new Liquid()

  it('filters on a string', function () {
    expect(engine.parseAndRenderSync('{{ s | first }}', { s: 'abc' })).toBe('a')
    expect(engine.parseAndRenderSync('{{ s | last }}', { s: 'abc' })).toBe('c')
    expect(engine.parseAndRenderSync('{{ s | slice: 0, 2 }}', { s: 'abc' })).toBe('ab')
    expect(engine.parseAndRenderSync('{{ s.size }}', { s: 'abc' })).toBe('3')
    expect(engine.parseAndRenderSync('{{ s | at: 1 }}', { s: 'abc' })).toBe('b')
    expect(engine.parseAndRenderSync('{{ s | at: -1 }}', { s: 'abc' })).toBe('c')
  })

  it('a sentence from a string list', function () {
    const src = '{{ list | array_to_sentence_string }}'
    expect(engine.parseAndRenderSync(src, { list: ['red', 'green', 'blue'] })).toBe('red, green, and blue')
    expect(engine.parseAndRenderSync(src, { list: ['red', 'green'] })).toBe('red and green')
    expect(engine.parseAndRenderSync(src, { list: ['red'] })).toBe('red')
  })
})
