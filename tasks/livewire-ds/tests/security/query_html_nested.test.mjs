import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('a nested address parameter cannot install page markup', () => {
  beforeEach(() => resetPage())

  it('does not install markup the server did not send', async () => {
    window.history.replaceState({}, '', query(bracket(['count', '__proto__', 'html'], '<div data-xss-marker>probe</div>')))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.html).toBeUndefined()
    expect(document.querySelector('[data-xss-marker]')).toBeNull()
  })
})
