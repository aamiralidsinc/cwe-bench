import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('address-bound values round-trip', () => {
  beforeEach(() => resetPage())

  it('reads nested, list and scalar values out of the address', async () => {
    window.history.replaceState({}, '', '/?filters[startDate]=2024-01-01&filters[endDate]=2024-09-05&items[0][0]=foo&date=2024-01-01&empty=')
    await boot()
    const history = window.Alpine.history

    const filters = history.track('filters', { startDate: '', endDate: '' })
    expect(filters.initial.startDate).toBe('2024-01-01')
    expect(filters.initial.endDate).toBe('2024-09-05')

    const items = history.track('items', [])
    expect(items.initial[0][0]).toBe('foo')

    expect(history.track('date', '').initial).toBe('2024-01-01')
    expect(history.track('empty', 'seed').initial).toBe('')
    expect(history.track('absent', 'seed').initial).toBe('seed')
  })
})
