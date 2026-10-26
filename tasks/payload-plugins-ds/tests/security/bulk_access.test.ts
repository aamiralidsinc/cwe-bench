import { describe, expect, it } from 'vitest'

import { GENERATED_ALT, USER, bodyText, buildWorld, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/generate/bulk'

function world(access: any = {}, localized = false) {
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
      ],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
        { alt: '', filename: 'secret-2.png', id: 901, mimeType: 'image/png' },
      ],
    },
    localized,
  })
}

function bulk(w: ReturnType<typeof world>, user: any, body: unknown) {
  return w.endpoint(PATH)(makeRequest(w, user, body))
}

describe('batch generation is limited to the requesting user', () => {
  it('does not write documents the caller cannot read', async () => {
    const w = world()
    const response = await bulk(w, USER, { collection: 'secret', ids: ['s1', 901] })
    const body = await readJson(response)

    expect(w.writesTo('secret')).toHaveLength(0)
    expect(response.ok && bodyText(body).includes(GENERATED_ALT)).toBe(false)
  })

  it('does not write documents the caller may read but may not change', async () => {
    const w = world({ mediaUpdate: () => false })
    const response = await bulk(w, USER, { collection: 'media', ids: ['m1', 'm2'] })
    await readJson(response)

    expect(w.writesTo('media')).toHaveLength(0)
  })

  it('does not write any of several inaccessible documents', async () => {
    const w = world()
    await readJson(await bulk(w, USER, { collection: 'secret', ids: ['s1', 901] }))
    expect(w.writesTo('secret')).toHaveLength(0)
  })

  it('does not write any locale of an inaccessible document', async () => {
    const w = world({}, true)
    const response = await bulk(w, USER, { collection: 'secret', ids: ['s1'] })
    await readJson(response)

    expect(w.writesTo('secret')).toHaveLength(0)
  })

  it('honours a document-scoped read constraint on every identifier', async () => {
    // m1 belongs to the caller; m2 belongs to someone else.
    const worldWithOwners = buildWorld({
      collections: [
        {
          slug: 'media',
          access: {
            read: ({ req }: any) =>
              req.user?.role === 'admin' ? true : { owner: { equals: req.user.id } },
            update: () => true,
          },
        },
        {
          slug: 'secret',
          access: { read: () => false, update: () => false },
        },
      ],
      docs: {
        media: [
          { alt: '', filename: 'mine.png', id: 'mine', mimeType: 'image/png', owner: 'user-1' },
          { alt: '', filename: 'theirs.png', id: 'theirs', mimeType: 'image/png', owner: 'user-2' },
        ],
        secret: [],
      },
    })
    const response = await worldWithOwners.endpoint(PATH)(
      makeRequest(worldWithOwners, USER, { collection: 'media', ids: ['mine', 'theirs'] }),
    )
    await readJson(response)

    expect(worldWithOwners.writesTo('media').map((write) => write.id)).not.toContain('theirs')
  })
})
