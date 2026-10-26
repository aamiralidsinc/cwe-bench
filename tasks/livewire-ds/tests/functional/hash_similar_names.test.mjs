import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, fragment, bracket, resetPage, delay } from '../support/page.mjs'

describe('fragment names that resemble a built-in name still bind', () => {
  beforeEach(() => resetPage())

  it('binds ordinary fragment names that resemble reserved ones', async () => {
    window.history.replaceState({}, '', '/#filters[constructorName]=x&filters[proto]=y&filters[prototypeName]=z')
    const holder = document.createElement('div')
    holder.setAttribute('x-data', "{ f: $hashQueryString('filters', {}) }")
    holder.innerHTML = '<span id="a" x-text="f.constructorName"></span><span id="b" x-text="f.proto"></span><span id="c" x-text="f.prototypeName"></span>'
    document.body.appendChild(holder)
    await boot()
    expect(document.querySelector('#a').textContent).toBe('x')
    expect(document.querySelector('#b').textContent).toBe('y')
    expect(document.querySelector('#c').textContent).toBe('z')
  })
})
