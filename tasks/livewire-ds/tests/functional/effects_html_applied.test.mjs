import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('server-sent markup is applied', () => {
  beforeEach(() => resetPage())

  it('applies markup the server sent', async () => {
    addComponent('target', { other: 1 }, { html: '<div data-server-markup data-ok="yes"></div>' })
    await boot()
    const el = document.querySelector('[data-server-markup]')
    expect(el).not.toBeNull()
    expect(el.getAttribute('data-ok')).toBe('yes')
  })
})
