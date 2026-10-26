import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot register a listener', () => {
  beforeEach(() => resetPage())

  it('does not register an event listener from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'listeners', '0'], 'lw-probe-listen'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    window.dispatchEvent(new CustomEvent('lw-probe-listen'))
    await delay(80)
    expect(globalThis.__requests.length).toBe(0)
  })
})
