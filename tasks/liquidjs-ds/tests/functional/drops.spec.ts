import { Liquid } from '../../src/liquid'
import { Drop } from '../../src/drop/drop'

class Greeter extends Drop {
  greeting () {
    return 'hello'
  }
}

class Fallback extends Drop {
  liquidMethodMissing (key: string | number) {
    return `missing:${key}`
  }
}

describe('custom template objects keep their own API', function () {
  const engine = new Liquid()

  it('a method on the class prototype still resolves', function () {
    expect(engine.parseAndRenderSync('{{ d.greeting }}', { d: new Greeter() })).toBe('hello')
  })

  it('the missing-name hook still resolves', function () {
    expect(engine.parseAndRenderSync('{{ d.anything }}', { d: new Fallback() })).toBe('missing:anything')
  })
})
