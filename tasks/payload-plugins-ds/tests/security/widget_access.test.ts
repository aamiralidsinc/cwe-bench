import { describe, expect, it } from 'vitest'

import { getAltTextHealthWidgetData } from '../../alt-text/src/utilities/altTextHealth.ts'
import { healthWorld } from '../harness/scenarios.ts'
import { ADMIN, USER, bodyText, makeRequest, readJson } from '../harness/world.ts'

describe('dashboard reporting data is limited to collections the caller may read', () => {
  it('does not include a collection the caller cannot read', async () => {
    const world = healthWorld()
    const data = await getAltTextHealthWidgetData(makeRequest(world, USER))

    expect(bodyText(data)).not.toContain('secret')
    expect(bodyText(data)).not.toContain('s1')
  })

  it('totals only the collections the caller may read', async () => {
    const world = healthWorld()
    const data = await getAltTextHealthWidgetData(makeRequest(world, USER))

    // The secret collection holds two documents; the media collection holds two.
    expect(data.totalDocs).toBe(2)
  })

  it('does not serve another user a complete report that was computed earlier', async () => {
    const world = healthWorld()
    await getAltTextHealthWidgetData(makeRequest(world, ADMIN))

    const data = await getAltTextHealthWidgetData(makeRequest(world, USER))
    expect(bodyText(data)).not.toContain('secret')
  })

  it('does not leak a collection through an error report', async () => {
    const world = healthWorld({ failFind: ['secret'] })
    const data = await getAltTextHealthWidgetData(makeRequest(world, USER))

    expect(bodyText(data)).not.toContain('secret')
  })
})
