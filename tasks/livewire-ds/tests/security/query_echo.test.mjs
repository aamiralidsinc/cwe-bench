import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot subscribe to a broadcast channel', () => {
  beforeEach(() => resetPage())

  it('does not subscribe to a channel from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'listeners', '0'], 'echo:private:orders,OrderShipped'),
    ))
    const calls = []
    const channel = kind => name => {
      calls.push([kind, name])
      return new Proxy({}, { get: () => (event) => calls.push([kind, name, String(event)]) })
    }
    globalThis.Echo = window.Echo = {
      channel: channel('channel'), private: channel('private'),
      encryptedPrivate: channel('encryptedPrivate'), join: channel('join'),
    }
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(calls).toEqual([])
  })
})
