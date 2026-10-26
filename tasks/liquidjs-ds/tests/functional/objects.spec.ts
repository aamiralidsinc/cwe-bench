import { Liquid } from '../../src/liquid'
import { OBJECT_MARKER, withObjectPrototype } from '../support/prototype'

describe('object members keep working', function () {
  const engine = new Liquid()

  it('own properties remain visible', function () {
    expect(engine.parseAndRenderSync('{{ o.name }}-{{ o.nested.value }}', {
      o: { name: 'alice', nested: { value: 'inner' } }
    })).toBe('alice-inner')
  })

  it('an own end name wins', function () {
    expect(engine.parseAndRenderSync('{{ o.first }}-{{ o.last }}', {
      o: { first: 'one', last: 'two' }
    })).toBe('one-two')
  })

  it('inherited properties stay hidden', function () {
    const out = withObjectPrototype(() => engine.parseAndRenderSync('{{ o.secret }}', { o: {} }))
    expect(out).toBe('')
    expect(out).not.toContain(OBJECT_MARKER)
  })
})
