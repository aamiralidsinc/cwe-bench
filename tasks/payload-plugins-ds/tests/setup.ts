import { beforeEach } from 'vitest'

import { __resetCache } from './harness/nextCacheStub.ts'

// The product's shared cache must not carry state from one test case to another.
beforeEach(() => {
  __resetCache()
})
