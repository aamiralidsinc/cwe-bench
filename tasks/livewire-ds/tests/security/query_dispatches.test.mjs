import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot dispatch an event', () => {
  beforeEach(() => resetPage())

  it('does not dispatch an event from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'dispatches', '0', 'name'], 'lw-probe-event'),
    ))
    let seen = false
    window.addEventListener('lw-probe-event', () => { seen = true })
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(seen).toBe(false)
  })
})
