import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('the same protection holds for a different bound property', () => {
  beforeEach(() => resetPage())

  it('does not install markup under another bound property', async () => {
    window.history.replaceState({}, '', query(bracket(['q', '__proto__', 'html'], '<div data-xss-marker>probe</div>')))
    addComponent('bound', { q: 0 }, { url: { q: 'q' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.html).toBeUndefined()
    expect(document.querySelector('[data-xss-marker]')).toBeNull()
  })
})
