import { describe, expect, it } from 'vitest'

import { ADMIN, GENERATED_ALT, GENERATED_KEYWORDS, USER, buildWorld, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/generate'

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
          read: ({ req }: any) => req.user?.role === 'admin',
          update: () => false,
        },
      },
    ],
    docs: {
      media: [
        { alt: 'A cat on a mat', filename: 'cat.png', id: 'm1', mimeType: 'image/png' },
        { alt: '', filename: 'dog.png', id: 501, mimeType: 'image/png' },
      ],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
      ],
    },
  })
}

describe('generation keeps working for a caller who may read or change the document', () => {
  it('returns generated alt text without saving it for a caller who may read the document', async () => {
    const w = world()
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', id: 'm1', locale: 'en', update: false }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.altText).toBe(GENERATED_ALT)
    expect(w.writesTo('media')).toHaveLength(0)
  })

  it('returns generated alt text for a numeric identifier', async () => {
    const w = world()
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', id: 501, locale: 'en', update: false }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.altText).toBe(GENERATED_ALT)
  })

  it('keeps preview available to a caller who may read but may not change the document', async () => {
    const w = world({ mediaUpdate: () => false })
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', id: 'm1', locale: 'en', update: false }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.altText).toBe(GENERATED_ALT)
    expect(w.writesTo('media')).toHaveLength(0)
  })

  it('saves alt text and keywords for a caller who may change the document', async () => {
    const w = world()
    const response = await w.endpoint(PATH)(
      makeRequest(w, USER, { collection: 'media', id: 'm1', locale: 'en', update: true }),
    )
    await readJson(response)

    expect(response.ok).toBe(true)
    const writes = w.writesTo('media')
    expect(writes).toHaveLength(1)
    expect(writes[0].data.alt).toBe(GENERATED_ALT)
    expect(writes[0].data.keywords).toEqual(GENERATED_KEYWORDS)
    expect(writes[0].locale).toBe('en')
  })

  it('lets an administrator generate for a document in a restricted collection', async () => {
    const w = world()
    const response = await w.endpoint(PATH)(
      makeRequest(w, ADMIN, { collection: 'secret', id: 's1', locale: 'en', update: false }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.altText).toBe(GENERATED_ALT)
  })
})
