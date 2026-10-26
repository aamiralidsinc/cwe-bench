import { describe, expect, it } from 'vitest'

import { IMPORTED_ALT, USER, bodyText, buildWorld, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/import'

function world(access: any = {}) {
  return buildWorld({
    collections: [
      {
        slug: 'media',
        access: {
          read: () => true,
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
      media: [{ alt: 'A cat on a mat', filename: 'cat.png', id: 'm1', mimeType: 'image/png' }],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
        { alt: 'SECRET-ALT-TWO', filename: 'secret-2.png', id: 901, mimeType: 'image/png' },
      ],
    },
  })
}

function importItems(w: ReturnType<typeof world>, body: unknown) {
  return w.endpoint(PATH)(makeRequest(w, USER, body))
}

describe('the import route is limited to the requesting user', () => {
  it('does not write caller-supplied alt text to a document the caller cannot change', async () => {
    const w = world()
    const response = await importItems(w, {
      collection: 'secret',
      items: [{ alt: IMPORTED_ALT, id: 's1', keywords: ['imported'] }],
    })
    const body = await readJson(response)

    expect(w.writesTo('secret')).toHaveLength(0)
    expect(response.ok && bodyText(body).includes(IMPORTED_ALT)).toBe(false)
  })

  it('does not write caller-supplied alt text to a numeric document identifier it cannot change', async () => {
    const w = world()
    await readJson(
      await importItems(w, {
        collection: 'secret',
        items: [{ alt: IMPORTED_ALT, id: 901 }],
      }),
    )

    expect(w.writesTo('secret')).toHaveLength(0)
  })

  it('does not write when the caller may read the collection but may not change a document', async () => {
    const w = world({ mediaUpdate: () => false })
    await readJson(
      await importItems(w, {
        collection: 'media',
        items: [{ alt: IMPORTED_ALT, id: 'm1' }],
      }),
    )

    expect(w.writesTo('media')).toHaveLength(0)
  })

  it('does not write any item when several identifiers are inaccessible', async () => {
    const w = world()
    await readJson(
      await importItems(w, {
        collection: 'secret',
        items: [
          { alt: IMPORTED_ALT, id: 's1' },
          { alt: IMPORTED_ALT, id: 901 },
        ],
      }),
    )

    expect(w.writesTo('secret')).toHaveLength(0)
  })
})
