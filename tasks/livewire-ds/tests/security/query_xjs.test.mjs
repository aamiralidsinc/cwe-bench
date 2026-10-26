import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot install an executable expression', () => {
  beforeEach(() => resetPage())

  it('does not execute an expression from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'xjs', '0', 'expression'], 'window.__lw_xjs = 1'),
      bracket(['count', '__proto__', 'xjs', '0', 'params'], ''),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.xjs).toBeUndefined()
    expect(window.__lw_xjs).toBeUndefined()
  })
})
