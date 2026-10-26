import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('server-sent scripts and expressions run', () => {
  beforeEach(() => resetPage())

  it('runs scripts and expressions the server sent', async () => {
    addComponent('target', { other: 1 }, {
      scripts: { probe: '<script>window.__ok_script = 1</script>' },
      xjs: [{ expression: 'window.__ok_xjs = 1', params: {} }],
    })
    await boot()
    expect(window.__ok_script).toBe(1)
    expect(window.__ok_xjs).toBe(1)
  })
})
