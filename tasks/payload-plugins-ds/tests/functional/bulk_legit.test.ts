import { describe, expect, it } from 'vitest'

import { GENERATED_ALT, USER, buildWorld, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/generate/bulk'

function world(options: { localized?: boolean; mediaRead?: any } = {}) {
  return buildWorld({
    collections: [
      {
        slug: 'media',
        access: { read: options.mediaRead ?? (() => true), update: () => true },
      },
      { slug: 'secret', access: { read: () => false, update: () => false } },
    ],
    docs: {
      media: [
        { alt: '', filename: 'cat.png', id: 'm1', mimeType: 'image/png', owner: 'user-1' },
        { alt: '', filename: 'dog.png', id: 'm2', mimeType: 'image/png', owner: 'user-1' },
        { alt: '', filename: 'bird.png', id: 'm3', mimeType: 'image/png', owner: 'user-2' },
      ],
      secret: [],
    },
    localized: options.localized,
  })
}

describe('batch generation keeps working for accessible documents', () => {
  it('updates every accessible document in the request', async () => {
    const w = world()
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', ids: ['m1', 'm2'] }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.updatedDocs).toBe(2)
    expect(body.erroredDocs).toEqual([])
    const writes = w.writesTo('media')
    expect(writes.map((write) => write.id).sort()).toEqual(['m1', 'm2'])
    expect(writes.every((write) => write.data.alt === GENERATED_ALT)).toBe(true)
  })

  it('updates every locale of every accessible document', async () => {
    const w = world({ localized: true })
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', ids: ['m1'] }),
    )
    await readJson(response)

    const writes = w.writesTo('media')
    expect(writes.map((write) => write.locale).sort()).toEqual(['de', 'en'])
  })

  it('processes the documents a scoped read rule admits', async () => {
    const w = world({
      mediaRead: ({ req }: any) =>
        req.user?.role === 'admin' ? true : { owner: { equals: req.user.id } },
    })
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', ids: ['m1', 'm3'] }),
    )
    await readJson(response)

    const written = w.writesTo('media').map((write) => write.id)
    expect(written).toContain('m1')
  })

  it('completes a request that covers many documents', async () => {
    const ids = Array.from({ length: 40 }, (_, index) => `batched-${index}`)
    const many = buildWorld({
      collections: [
        { slug: 'media', access: { read: () => true, update: () => true } },
        { slug: 'secret', access: { read: () => false, update: () => false } },
      ],
      docs: {
        media: ids.map((id) => ({ alt: '', filename: `${id}.png`, id, mimeType: 'image/png' })),
        secret: [],
      },
    })
    const response = await many.endpoint(PATH)(
      makeRequest(many, USER, { collection: 'media', ids }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.updatedDocs).toBe(ids.length)
    expect(many.writesTo('media')).toHaveLength(ids.length)
  })
})
