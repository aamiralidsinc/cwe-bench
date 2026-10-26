import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('instructions from the address cannot survive a re-save', () => {
  beforeEach(() => resetPage())

  it('does not replay address values after the page re-saves its state', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'scripts', 'probe'], '<script>window.__lw_inscribe = 1</script>'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    const target = addComponent('target', { other: 1 }, {})
    await boot()

    document.dispatchEvent(new CustomEvent('alpine:navigating'))
    await delay(30)
    const inscribed = target.getAttribute('wire:effects')

    // Coming back to a cached page: the address is gone, so the shared prototype is
    // clean; only what the page wrote into its own DOM can still run.
    resetPage('/')
    const replay = document.createElement('div')
    replay.setAttribute('wire:id', 'replay')
    replay.setAttribute('wire:snapshot', JSON.stringify({ data: { other: 2 }, memo: { id: 'replay', name: 'probe', children: {} }, checksum: 'x' }))
    replay.setAttribute('wire:effects', inscribed)
    document.body.appendChild(replay)
    await delay(150)

    expect(window.__lw_inscribe).toBeUndefined()
  })
})
