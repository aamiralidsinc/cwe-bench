import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('an ordinary page leaves shared objects untouched', () => {
  beforeEach(() => resetPage())

  it('leaves the shared prototypes untouched', async () => {
    window.history.replaceState({}, '', '/?filters[startDate]=2024-01-01&filters[endDate]=2024-09-05')
    addComponent('bound', { filters: {} }, { url: { filters: 'filters' } })
    addComponent('target', { other: 1 }, {})
    await boot()
    expect(Object.prototype.html).toBeUndefined()
    expect(Object.prototype.scripts).toBeUndefined()
    expect([].html).toBeUndefined()
  })
})
