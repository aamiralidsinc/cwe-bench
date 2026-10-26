import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('a named prefix before a prototype segment is still refused', () => {
  beforeEach(() => resetPage())

  it('does not install markup through a named prefix', async () => {
    window.history.replaceState({}, '', query(bracket(['count', 'filters', '__proto__', 'html'], '<div data-xss-marker>probe</div>')))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.html).toBeUndefined()
    expect(document.querySelector('[data-xss-marker]')).toBeNull()
  })
})
