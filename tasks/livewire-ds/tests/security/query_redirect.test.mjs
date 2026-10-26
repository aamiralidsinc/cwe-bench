import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot navigate the page', () => {
  beforeEach(() => resetPage())

  it('does not redirect from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'redirect'], '#lw-probe-redirect'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(window.location.hash).not.toBe('#lw-probe-redirect')
  })
})
