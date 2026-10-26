import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot start a download', () => {
  beforeEach(() => resetPage())

  it('does not start a download from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'download', 'content'], 'eA=='),
      bracket(['count', '__proto__', 'download', 'contentType'], 'text/plain'),
      bracket(['count', '__proto__', 'download', 'name'], 'lw-probe.txt'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    const Livewire = await boot()
    try { await Livewire.find('target').probe() } catch (e) {}
    await delay(80)
    expect(globalThis.__objectUrls.length).toBe(0)
  })
})
