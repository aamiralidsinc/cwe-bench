import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('a server-sent return value is delivered', () => {
  beforeEach(() => resetPage())

  it('delivers a value the server returned', async () => {
    addComponent('target', { other: 1 }, {})
    globalThis.__responseEffects = { returns: ['legit-return'] }
    const Livewire = await boot()
    const value = await Livewire.find('target').probe()
    expect(value).toBe('legit-return')
  })
})
