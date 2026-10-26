import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('server-sent listeners and dispatches work', () => {
  beforeEach(() => resetPage())

  it('registers listeners and dispatches events the server sent', async () => {
    let dispatched = false
    window.addEventListener('lw-legit-dispatched', () => { dispatched = true })
    addComponent('target', { other: 1 }, {
      listeners: ['lw-legit-listen'],
      dispatches: [{ name: 'lw-legit-dispatched' }],
    })
    await boot()
    expect(dispatched).toBe(true)
    window.dispatchEvent(new CustomEvent('lw-legit-listen'))
    await delay(80)
    expect(globalThis.__requests.length).toBe(1)
  })
})
