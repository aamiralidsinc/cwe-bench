import { describe, expect, it } from 'vitest'
import { createEvent } from 'h3'

import { getRouteRules } from '#app/composables/manifest'
import { isCachedPayloadRoute } from '#app/composables/payload'

describe('route rules apply to the route they name, whatever the request case', () => {
  it('applies an exact mixed-case rule to its own path', () => {
    expect(getRouteRules({ path: '/Admin/Dashboard' })).toMatchObject({ appMiddleware: { auth: true } })
  })

  it('applies an exact mixed-case rule to every casing of the path', () => {
    expect(getRouteRules({ path: '/admin/dashboard' })).toMatchObject({ appMiddleware: { auth: true } })
    expect(getRouteRules({ path: '/ADMIN/DASHBOARD' })).toMatchObject({ appMiddleware: { auth: true } })
    expect(getRouteRules({ path: '/aDmIn/DaShBoArD' })).toMatchObject({ appMiddleware: { auth: true } })
  })

  it('applies a mixed-case wildcard rule to every casing of a matching path', () => {
    expect(getRouteRules({ path: '/secret/docs/guide' })).toMatchObject({ appMiddleware: { auth: true }, ssr: false })
    expect(getRouteRules({ path: '/SECRET/DOCS/GUIDE' })).toMatchObject({ appMiddleware: { auth: true }, ssr: false })
    expect(getRouteRules({ path: '/Secret/Docs/deep/page' })).toMatchObject({ appMiddleware: { auth: true } })
  })

  it('applies a mixed-case rule to the deprecated string argument form', () => {
    expect(getRouteRules('/Legacy/Home')).toMatchObject({ redirect: '/target' })
    expect(getRouteRules('/legacy/home')).toMatchObject({ redirect: '/target' })
  })

  it('applies a mixed-case rule to a request event', () => {
    const event = createEvent({ url: '/SECRET/DOCS/EVENT', method: 'GET', headers: {} } as any, {} as any)
    expect(getRouteRules(event as any)).toMatchObject({ appMiddleware: { auth: true }, ssr: false })
  })

  it('uses an applicable cache rule for a differently-cased route', () => {
    expect(isCachedPayloadRoute('/data/feed')).toBe(true)
    expect(isCachedPayloadRoute('/DATA/FEED')).toBe(true)
    expect(isCachedPayloadRoute('/data/feed?page=2')).toBe(true)
  })
})
