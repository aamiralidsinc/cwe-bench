import { describe, expect, it } from 'vitest'

import { GENERATED_ALT, IMPORTED_ALT, USER, buildWorld, makeRequest, readJson } from '../harness/world.ts'

function world() {
  return buildWorld({
    collections: [
      { slug: 'media', access: { read: () => true, update: () => true } },
      { slug: 'secret', access: { read: () => false, update: () => false } },
    ],
    docs: {
      media: [
        { alt: 'PUBLIC-ALT-ONE', filename: 'cat.png', id: 'm1', mimeType: 'image/png' },
        { alt: '', filename: 'dog.png', id: 'm2', mimeType: 'image/png' },
        { filename: 'bird.png', id: 'm3', mimeType: 'image/png' },
      ],
      secret: [],
    },
  })
}

describe('the auxiliary routes keep working for accessible documents', () => {
  it('fills the missing alt text of a collection the caller may change', async () => {
    const w = world()
    const response = await w.endpoint('/alt-text-plugin/generate/missing')(
      makeRequest(w, USER, { collection: 'media' }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.totalDocs).toBe(2)
    expect(body.updatedDocs).toBe(2)
    const writes = w.writesTo('media')
    expect(writes.map((write) => write.id).sort()).toEqual(['m2', 'm3'])
    expect(writes.every((write) => write.data.alt === GENERATED_ALT)).toBe(true)
  })

  it('exports the alt text of a collection the caller may read', async () => {
    const w = world()
    const response = await w.endpoint('/alt-text-plugin/export')(
      makeRequest(w, USER, { collection: 'media' }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    const exported = body.docs.find((doc: any) => doc.id === 'm1')
    expect(exported.alt).toBe('PUBLIC-ALT-ONE')
    expect(exported.filename).toBe('cat.png')
  })

  it('applies caller-supplied alt text to a document the caller may change', async () => {
    const w = world()
    const response = await w.endpoint('/alt-text-plugin/import')(
      makeRequest(w, USER, {
        collection: 'media',
        items: [{ alt: IMPORTED_ALT, id: 'm1', keywords: ['imported'] }],
      }),
    )
    const body = await readJson(response)

    expect(response.ok).toBe(true)
    expect(body.updatedDocs).toBe(1)
    const writes = w.writesTo('media')
    expect(writes).toHaveLength(1)
    expect(writes[0].data.alt).toBe(IMPORTED_ALT)
    expect(writes[0].data.keywords).toEqual(['imported'])
  })
})
