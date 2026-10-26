import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an address parameter cannot install a script', () => {
  beforeEach(() => resetPage())

  it('does not run a script from the address', async () => {
    window.history.replaceState({}, '', query(
      bracket(['count', '__proto__', 'scripts', 'probe'], '<script>window.__lw_scripts = 1</script>'),
    ))
    addComponent('bound', { count: 0 }, { url: { count: 'count' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.scripts).toBeUndefined()
    expect(window.__lw_scripts).toBeUndefined()
  })
})
