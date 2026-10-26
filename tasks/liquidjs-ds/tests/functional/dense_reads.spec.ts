import { Liquid } from '../../src/liquid'
import { dense, withArrayPrototype } from '../support/prototype'

describe('ordinary sequences keep working', function () {
  const engine = new Liquid()
  const arr = dense()

  it('indexes and end names', function () {
    expect(engine.parseAndRenderSync('{{ arr[0] }}', { arr })).toBe('own-zero')
    expect(engine.parseAndRenderSync('{{ arr[-1] }}', { arr })).toBe('own-two')
    expect(engine.parseAndRenderSync('{{ arr[-3] }}', { arr })).toBe('own-zero')
    expect(engine.parseAndRenderSync('{{ arr.first }}', { arr })).toBe('own-zero')
    expect(engine.parseAndRenderSync('{{ arr.last }}', { arr })).toBe('own-two')
    expect(engine.parseAndRenderSync('{{ arr | first }}', { arr })).toBe('own-zero')
    expect(engine.parseAndRenderSync('{{ arr | last }}', { arr })).toBe('own-two')
    expect(engine.parseAndRenderSync('{{ arr.size }}', { arr })).toBe('3')
    expect(engine.parseAndRenderSync('{{ arr.length }}', { arr })).toBe('3')
  })

  it('own elements next to unrelated prototype values stay visible', function () {
    const out = withArrayPrototype(() => engine.parseAndRenderSync(
      '{{ arr[-1] }}|{{ arr.first }}|{{ arr | last }}|{{ arr.size }}', { arr }))
    expect(out).toBe('own-two|own-zero|own-two|3')
  })
})
