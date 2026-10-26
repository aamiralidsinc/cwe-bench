import { describe, expect, it } from 'vitest'

import { GENERATED_ALT, USER, bodyText, buildWorld, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/generate/missing'

function world(access: any = {}) {
  return buildWorld({
    collections: [
      {
        slug: 'media',
        access: {
          read: access.mediaRead ?? (() => true),
          update: access.mediaUpdate ?? (() => true),
        },
      },
      {
        slug: 'secret',
        access: {
          read: access.secretRead ?? (() => false),
          update: access.secretUpdate ?? (() => false),
        },
      },
    ],
    docs: {
      media: [
        { alt: 'A cat on a mat', filename: 'cat.png', id: 'm1', mimeType: 'image/png' },
        { alt: '', filename: 'dog.png', id: 'm2', mimeType: 'image/png' },
        { filename: 'bird.png', id: 'm3', mimeType: 'image/png' },
      ],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
        { alt: '', filename: 'secret-2.png', id: 's2', mimeType: 'image/png' },
        { filename: 'secret-3.png', id: 's3', mimeType: 'image/png' },
      ],
    },
  })
}

function backfill(w: ReturnType<typeof world>, body: unknown) {
  return w.endpoint(PATH)(makeRequest(w, USER, body))
}

describe('the gap-filling route is limited to the requesting user', () => {
  it('does not select or write documents in a collection the caller cannot read', async () => {
    const w = world()
    const response = await backfill(w, { collection: 'secret' })
    const body = await readJson(response)

    expect(w.writesTo('secret')).toHaveLength(0)
    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
    expect(response.ok && (body.totalDocs ?? 0) > 0).toBe(false)
  })

  it('does not write documents the caller may read but may not change', async () => {
    const w = world({ mediaUpdate: () => false })
    await readJson(await backfill(w, { collection: 'media' }))

    expect(w.writesTo('media')).toHaveLength(0)
  })
})
