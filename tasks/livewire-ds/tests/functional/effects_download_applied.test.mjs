import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('a server-sent download starts', () => {
  beforeEach(() => resetPage())

  it('starts a download the server sent', async () => {
    addComponent('target', { other: 1 }, {})
    globalThis.__responseEffects = {
      returns: [],
      download: { content: 'eA==', contentType: 'text/plain', name: 'legit.txt' },
    }
    const Livewire = await boot()
    try { await Livewire.find('target').probe() } catch (e) {}
    await delay(80)
    expect(globalThis.__objectUrls.length).toBe(1)
  })
})
