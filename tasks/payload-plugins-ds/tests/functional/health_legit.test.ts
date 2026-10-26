import { describe, expect, it } from 'vitest'

import {
  getAltTextHealth,
  getAltTextHealthWidgetData,
} from '../../alt-text/src/utilities/altTextHealth.ts'
import { healthWorld } from '../harness/scenarios.ts'
import { ADMIN, USER, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/health'

describe('reporting keeps working for collections the caller may read', () => {
  it('reports every readable collection with its counts to an administrator', async () => {
    const world = healthWorld()
    const response = await world.endpoint(PATH)(makeRequest(world, ADMIN))
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    const bySlug = Object.fromEntries(
      body.collections.map((entry: any) => [entry.collection, entry]),
    )
    expect(bySlug.media.totalDocs).toBe(2)
    expect(bySlug.media.completeDocs).toBe(1)
    expect(bySlug.secret.totalDocs).toBe(2)
  })

  it('shows a scoped reader the collection-wide entry for the collection', async () => {
    // A read rule limited to some documents still grants collection-wide information.
    const scoped = healthWorld({
      mediaRead: ({ req }: any) =>
        req.user?.role === 'admin' ? true : { owner: { equals: req.user.id } },
      secretRead: () => false,
    })

    const response = await scoped.endpoint(PATH)(makeRequest(scoped, USER))
    const body = await readJson(response)
    const slugs = body.collections.map((entry: any) => entry.collection)

    expect(response.ok).toBe(true)
    expect(slugs).toContain('media')
  })

  it('still shows an administrator the complete report after another user warmed it', async () => {
    const world = healthWorld()
    await readJson(await world.endpoint(PATH)(makeRequest(world, USER)))

    const response = await world.endpoint(PATH)(makeRequest(world, ADMIN))
    const body = await readJson(response)
    const slugs = body.collections.map((entry: any) => entry.collection)

    expect(slugs).toContain('media')
    expect(slugs).toContain('secret')
  })

  it('keeps the lower-level scan available to a caller who may read a collection', async () => {
    const world = healthWorld()
    const scan = await getAltTextHealth(makeRequest(world, USER))

    expect(scan.collections.map((entry) => entry.collection)).toContain('media')
  })

  it('totals every readable collection in the dashboard data', async () => {
    const world = healthWorld()
    const data = await getAltTextHealthWidgetData(makeRequest(world, ADMIN))

    expect(data.totalDocs).toBe(4)
    expect(data.collections.map((entry: any) => entry.collection).sort()).toEqual([
      'media',
      'secret',
    ])
  })
})
