import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, fragment, bracket, resetPage, delay } from '../support/page.mjs'

describe('a nested fragment parameter cannot install page markup', () => {
  beforeEach(() => resetPage())

  it('does not install markup the server did not send', async () => {
    window.history.replaceState({}, '', fragment(bracket(['filters', '__proto__', 'html'], '<div data-xss-marker>probe</div>')))
    
    const holder = document.createElement('div')
    holder.setAttribute('x-data', "{ filters: $hashQueryString('filters', {}) }")
    document.body.appendChild(holder)

    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.html).toBeUndefined()
    expect(document.querySelector('[data-xss-marker]')).toBeNull()
  })
})
