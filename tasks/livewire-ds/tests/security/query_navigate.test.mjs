import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot force a page visit', () => {
  beforeEach(() => resetPage())

  it('does not visit a page named by the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'redirect'], '/lw-probe-next'),
      bracket(['count', '__proto__', 'redirectUsingNavigate'], '1'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    await delay(120)
    expect(globalThis.__pageFetches.some(url => String(url).includes('/lw-probe-next'))).toBe(false)
  })
})
