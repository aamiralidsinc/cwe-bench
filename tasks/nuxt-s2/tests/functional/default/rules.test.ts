import { describe, expect, it } from 'vitest'

import { getRouteRules } from '#app/composables/manifest'
import { isCachedPayloadRoute, isPrerendered } from '#app/composables/payload'

describe('route-rule matching that works today keeps working', () => {
  it('matches a lowercase rule for its own path', () => {
    expect(getRouteRules({ path: '/lower/exact' })).toMatchObject({ redirect: '/target' })
  })

  it('matches a lowercase wildcard rule for every casing of a path', () => {
    expect(getRouteRules({ path: '/lower/case/thing' })).toMatchObject({ ssr: false })
    expect(getRouteRules({ path: '/LOWER/CASE/THING' })).toMatchObject({ ssr: false })
  })

  it('merges overlapping rules with the more specific rule taking precedence', () => {
    expect(getRouteRules({ path: '/pre/spa/thing' })).toMatchObject({ prerender: true, ssr: false })
    expect(getRouteRules({ path: '/pre/thing' })).toMatchObject({ prerender: true })
    expect(getRouteRules({ path: '/pre/thing' })).not.toHaveProperty('ssr')
  })

  it('keeps the rule value normalisation the public lookup provides', () => {
    expect(getRouteRules({ path: '/app/middleware' })).toMatchObject({ appMiddleware: { auth: true } })
    expect(getRouteRules({ path: '/app/middleware-list' })).toMatchObject({ appMiddleware: { auth: true, audit: true } })
    expect(getRouteRules({ path: '/app/layout' })).toMatchObject({ appLayout: 'custom' })
  })

  it('keeps cache rules visible as payload rules', () => {
    expect(getRouteRules({ path: '/data/feed' })).toMatchObject({ payload: true })
    expect(isCachedPayloadRoute('/data/feed')).toBe(true)
    expect(isCachedPayloadRoute('/data/feed?page=2')).toBe(true)
    expect(isCachedPayloadRoute('/some/other/page')).toBe(false)
  })

  it('keeps prerender decisions bound to the prerender rule', async () => {
    expect(await isPrerendered('/pre/thing')).toBe(true)
    expect(await isPrerendered('/lower/case/thing')).toBe(false)
    expect(await isPrerendered('/not/configured')).toBe(false)
  })

  it('returns an empty result for a path that no rule names', () => {
    expect(getRouteRules({ path: '/not/configured' })).toEqual({})
    expect(getRouteRules('/not/configured')).toEqual({})
  })
})
