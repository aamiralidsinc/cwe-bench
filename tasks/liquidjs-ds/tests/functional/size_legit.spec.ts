import { Liquid } from '../../src/liquid'

describe('structural sizes keep working', function () {
  const engine = new Liquid()

  it('sequence, string and object', function () {
    expect(engine.parseAndRenderSync('{{ a.size }}', { a: ['x', 'y', 'z'] })).toBe('3')
    expect(engine.parseAndRenderSync('{{ a.length }}', { a: ['x', 'y', 'z'] })).toBe('3')
    expect(engine.parseAndRenderSync('{{ s.size }}', { s: 'abcd' })).toBe('4')
    expect(engine.parseAndRenderSync('{{ o.size }}', { o: { one: 1, two: 2 } })).toBe('2')
  })

  it('set and map', function () {
    expect(engine.parseAndRenderSync('{{ s.size }}', { s: new Set([1, 2, 3]) })).toBe('3')
    expect(engine.parseAndRenderSync('{{ m.size }}', { m: new Map([['a', 1], ['b', 2]]) })).toBe('2')
  })

  it('an own size property wins', function () {
    expect(engine.parseAndRenderSync('{{ o.size }}', { o: { size: 7 } })).toBe('7')
  })
})
