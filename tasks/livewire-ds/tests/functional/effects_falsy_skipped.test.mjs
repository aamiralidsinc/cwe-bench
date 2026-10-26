import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('empty or absent instructions stay skipped', () => {
  beforeEach(() => resetPage())

  it('does nothing for empty instructions', async () => {
    const target = addComponent('target', { other: 1 }, {
      html: null, scripts: null, js: null, xjs: null, listeners: [], dispatches: [],
      redirect: null, download: null, returns: [], hotReload: [], url: null,
    })
    await boot()
    expect(target.textContent).toBe('target')
    expect(globalThis.__requests.length).toBe(0)
    expect(globalThis.__objectUrls.length).toBe(0)
    expect(window.location.hash).toBe('')
  })
})
