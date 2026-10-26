import { describe, expect, it } from 'vitest'

import {
  ADMIN,
  GENERATED_ALT,
  USER,
  bodyText,
  buildWorld,
  makeRequest,
  readJson,
} from '../harness/world.ts'

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
          read: access.secretRead ?? (({ req }: any) => req.user?.role === 'admin'),
          update: access.secretUpdate ?? (() => false),
        },
      },
    ],
    docs: {
      media: [
        { alt: 'A cat on a mat', filename: 'cat.png', id: 'm1', mimeType: 'image/png' },
        { alt: '', filename: 'dog.png', id: 'm2', mimeType: 'image/png' },
        { alt: '', filename: 'bird.png', id: 501, mimeType: 'image/png' },
      ],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
        { alt: '', filename: 'secret-2.png', id: 901, mimeType: 'image/png' },
      ],
    },
  })
}

function generate(w: ReturnType<typeof world>, user: any, body: unknown) {
  return w.endpoint(PATH)(makeRequest(w, user, body))
}

describe('single-image generation is limited to the requesting user', () => {
  it('does not return generated alt text for a document the caller cannot read', async () => {
    const w = world()
    const response = await generate(w, USER, {
      collection: 'secret',
      id: 's1',
      locale: 'en',
      update: false,
    })
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
  })

  it('does not return generated alt text for a numeric identifier the caller cannot read', async () => {
    const w = world()
    const response = await generate(w, USER, {
      collection: 'secret',
      id: 901,
      locale: 'en',
      update: false,
    })
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
  })

  it('does not write alt text to a document the caller cannot change', async () => {
    const w = world()
    const response = await generate(w, USER, {
      collection: 'secret',
      id: 's1',
      locale: 'en',
      update: true,
    })
    const body = await readJson(response)

    expect(w.writesTo('secret')).toHaveLength(0)
    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
  })

  it('does not write when the caller may read the document but may not change it', async () => {
    const w = world({ mediaUpdate: () => false })
    const response = await generate(w, USER, {
      collection: 'media',
      id: 'm1',
      locale: 'en',
      update: true,
    })
    const body = await readJson(response)

    expect(w.writesTo('media')).toHaveLength(0)
    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
  })

  it('does not return a document the caller cannot read even to an authenticated administrator of another collection', async () => {
    // A second authenticated identity with no special role is still denied.
    const w = world()
    const response = await generate(w, { id: 'other-1', role: 'editor' }, {
      collection: 'secret',
      id: 's1',
      locale: 'en',
      update: false,
    })
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
  })
})
