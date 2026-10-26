import { describe, expect, it } from 'vitest'

import { getRouteRules } from '#app/composables/manifest'
import { isPrerendered } from '#app/composables/payload'

describe('with case-sensitive route matching, rules are bound to their own spelling', () => {
  it('applies a mixed-case rule to its exact path', () => {
    expect(getRouteRules({ path: '/Admin/Dashboard' })).toMatchObject({
      appMiddleware: { auth: true },
      prerender: true,
    })
  })

  it('does not let a rule configured for one spelling reach another spelling', () => {
    expect(getRouteRules({ path: '/Legacy/Home' })).not.toHaveProperty('ssr')
    expect(getRouteRules({ path: '/LEGACY/HOME' })).not.toHaveProperty('ssr')
  })

  it('keeps a prerender decision on the route it was configured for', async () => {
    expect(await isPrerendered('/Admin/Dashboard')).toBe(true)
  })
})
