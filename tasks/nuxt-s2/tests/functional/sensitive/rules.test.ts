import { describe, expect, it } from 'vitest'

import { getRouteRules } from '#app/composables/manifest'

describe('with case-sensitive route matching, unrelated spellings stay unrelated', () => {
  it('does not apply a rule configured for one casing to another casing', () => {
    expect(getRouteRules({ path: '/admin/dashboard' })).toEqual({})
    expect(getRouteRules({ path: '/ADMIN/DASHBOARD' })).toEqual({})
  })

  it('still applies a rule to its own exact spelling', () => {
    expect(getRouteRules({ path: '/lower/case' })).toMatchObject({ ssr: false })
  })

  it('returns an empty result for a path that no rule names', () => {
    expect(getRouteRules({ path: '/lower/case/deeper' })).toEqual({})
  })
})
