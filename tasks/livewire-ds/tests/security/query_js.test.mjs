import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot define a callable action', () => {
  beforeEach(() => resetPage())

  it('does not define an action from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'js', 'probe'], 'window.__lw_js = 1'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    const Livewire = await boot()
    const wire = Livewire.find('target')
    try { await wire.probe() } catch (e) {}
    expect(window.__lw_js).toBeUndefined()
  })
})
