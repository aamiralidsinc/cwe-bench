import { describe, it, expect, beforeEach } from 'vitest'
import { addComponent, boot, query, bracket, resetPage, delay } from '../support/page.mjs'

describe('names that only resemble a built-in name still bind', () => {
  beforeEach(() => resetPage())

  it('binds ordinary names that resemble reserved ones', async () => {
    window.history.replaceState({}, '', '/?filters[constructorName]=x&filters[proto]=y&filters[prototypeName]=z')
    await boot()
    const initial = window.Alpine.history.track('filters', {}).initial
    expect(initial.constructorName).toBe('x')
    expect(initial.proto).toBe('y')
    expect(initial.prototypeName).toBe('z')
  })
})
