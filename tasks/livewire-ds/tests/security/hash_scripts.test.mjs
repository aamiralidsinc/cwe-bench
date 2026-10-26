import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, fragment, bracket, resetPage, delay } from '../support/page.mjs'

describe('a fragment parameter cannot install a script', () => {
  beforeEach(() => resetPage())

  it('does not run a script from the fragment', async () => {
    window.history.replaceState({}, '', fragment(
      bracket(['filters', '__proto__', 'scripts', 'probe'], '<script>window.__lw_hash_scripts = 1</script>'),
    ))
    const holder = document.createElement('div')
    holder.setAttribute('x-data', "{ filters: $hashQueryString('filters', {}) }")
    document.body.appendChild(holder)
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.scripts).toBeUndefined()
    expect(window.__lw_hash_scripts).toBeUndefined()
  })
})
