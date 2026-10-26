import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, fragment, bracket, resetPage, delay } from '../support/page.mjs'

describe('fragment-bound values keep working', () => {
  beforeEach(() => resetPage())

  it('renders ordinary nested fragment values', async () => {
    window.history.replaceState({}, '', '/#filters[from]=a&filters[to]=b&items[0][0]=foo')
    const holder = document.createElement('div')
    holder.setAttribute('x-data', "{ f: $hashQueryString('filters', {}), i: $hashQueryString('items', {}) }")
    holder.innerHTML = '<span id="from" x-text="f.from"></span><span id="to" x-text="f.to"></span><span id="item" x-text="i[0][0]"></span>'
    document.body.appendChild(holder)
    await boot()
    expect(document.querySelector('#from').textContent).toBe('a')
    expect(document.querySelector('#to').textContent).toBe('b')
    expect(document.querySelector('#item').textContent).toBe('foo')
  })
})
