import { describe, expect, it } from 'vitest'

import { getAltTextHealth } from '../../alt-text/src/utilities/altTextHealth.ts'
import { healthWorld } from '../harness/scenarios.ts'
import { ADMIN, USER, bodyText, makeRequest, readJson } from '../harness/world.ts'

describe('the health response is limited to collections the caller may read', () => {
  it('does not include a collection the caller cannot read', async () => {
    const world = healthWorld()
    const response = await world.endpoint('/alt-text-plugin/health')(makeRequest(world, USER))
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('secret')).toBe(false)
    expect(response.ok && bodyText(body).includes('s1')).toBe(false)
  })

  it('does not include the lower-level scan for a collection the caller cannot read', async () => {
    const world = healthWorld()
    const scan = await getAltTextHealth(makeRequest(world, USER))

    expect(scan.collections.map((entry) => entry.collection)).not.toContain('secret')
  })

  it('does not serve another user a complete scan that was computed earlier', async () => {
    const world = healthWorld()
    // An administrator's request populates any shared result first.
    await readJson(await world.endpoint('/alt-text-plugin/health')(makeRequest(world, ADMIN)))

    const response = await world.endpoint('/alt-text-plugin/health')(makeRequest(world, USER))
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('secret')).toBe(false)
    expect(response.ok && bodyText(body).includes('s1')).toBe(false)
  })

  it('does not leak a collection through a scan error report', async () => {
    const world = healthWorld({ failFind: ['secret'] })
    const response = await world.endpoint('/alt-text-plugin/health')(makeRequest(world, USER))
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('secret')).toBe(false)
  })

  it('treats a throwing read rule as denial', async () => {
    const world = healthWorld({
      secretRead: () => {
        throw new Error('Forbidden')
      },
    })
    const response = await world.endpoint('/alt-text-plugin/health')(makeRequest(world, USER))
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('secret')).toBe(false)
  })
})
