import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('a server-sent redirect is followed', () => {
  beforeEach(() => resetPage())

  it('follows a redirect the server sent', async () => {
    addComponent('target', { other: 1 }, { redirect: '#legit-redirect' })
    await boot()
    expect(window.location.hash).toBe('#legit-redirect')
  })
})
