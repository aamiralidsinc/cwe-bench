import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('nested values are written back to the address', () => {
  beforeEach(() => resetPage())

  it('writes nested object and list values in bracket notation', async () => {
    window.history.replaceState({}, '', '/')
    await boot()
    const history = window.Alpine.history

    const filters = history.track('filters', { startDate: '', endDate: '' })
    filters.replace({ startDate: 'a b', endDate: 'c,d' })
    const written = new URLSearchParams(window.location.search)
    expect(written.get('filters[startDate]')).toBe('a b')
    expect(written.get('filters[endDate]')).toBe('c,d')

    const items = history.track('items', [])
    items.replace([['foo', 'bar']])
    const writtenItems = new URLSearchParams(window.location.search)
    expect(writtenItems.get('items[0][0]')).toBe('foo')
    expect(writtenItems.get('items[0][1]')).toBe('bar')
  })
})
