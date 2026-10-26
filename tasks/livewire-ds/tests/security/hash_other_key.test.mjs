import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, fragment, bracket, resetPage, delay } from '../support/page.mjs'

describe('the same fragment protection holds for any bound name', () => {
  beforeEach(() => resetPage())

  it('does not install markup under another bound name', async () => {
    window.history.replaceState({}, '', fragment(
      bracket(['query', '__proto__', 'html'], '<div data-xss-marker>probe</div>'),
    ))
    const holder = document.createElement('div')
    holder.setAttribute('x-data', "{ q: $hashQueryString('query', {}) }")
    document.body.appendChild(holder)
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.html).toBeUndefined()
    expect(document.querySelector('[data-xss-marker]')).toBeNull()
  })
})
