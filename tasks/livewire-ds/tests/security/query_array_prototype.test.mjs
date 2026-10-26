import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage } from '../support/page.mjs'

describe('an address parameter cannot replace an array prototype', () => {
  beforeEach(() => resetPage())

  it('does not replace the prototype of a list built from the address', async () => {
    window.history.replaceState({}, '', query(bracket(['count', '0', '__proto__', 'html'], '<div data-xss-marker>probe</div>')))
    addComponent('bound', { count: [] }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()

    expect([].html).toBeUndefined()

    // The public entry point that reads the address: what it hands back must not
    // carry a replaced prototype.
    const tracked = window.Alpine.history.track('count', [])
    const built = tracked.initial
    expect(built).toBeDefined()
    expect(Object.getPrototypeOf(built)).toBe(Array.isArray(built) ? Array.prototype : Object.prototype)
    expect(document.querySelector('[data-xss-marker]')).toBeNull()
  })
})
