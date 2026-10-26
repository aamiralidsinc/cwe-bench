import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot supply a returned value', () => {
  beforeEach(() => resetPage())

  it('does not resolve a call with a value from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'returns', '0'], 'attacker-return'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    globalThis.__responseEffects = {}
    const Livewire = await boot()
    const value = await Promise.race([
      Livewire.find('target').probe().then(result => result),
      delay(400).then(() => 'no-return-sent'),
    ])
    expect(value).not.toBe('attacker-return')
  })
})
