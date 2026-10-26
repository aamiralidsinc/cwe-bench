import { describe, expect, it } from 'vitest'

import { USER, bodyText, buildWorld, makeRequest, readJson } from '../harness/world.ts'

const PATH = '/alt-text-plugin/export'

function world(access: any = {}) {
  return buildWorld({
    collections: [
      {
        slug: 'media',
        access: {
          read: access.mediaRead ?? (() => true),
          update: () => true,
        },
      },
      {
        slug: 'secret',
        access: {
          read: access.secretRead ?? (() => false),
          update: () => false,
        },
      },
    ],
    docs: {
      media: [
        {
          alt: 'PUBLIC-ALT-ONE',
          filename: 'cat.png',
          id: 'm1',
          mimeType: 'image/png',
          owner: 'user-1',
        },
        {
          alt: 'SOMEONE-ELSES-ALT',
          filename: 'dog.png',
          id: 'm2',
          mimeType: 'image/png',
          owner: 'user-2',
        },
      ],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
        { alt: 'SECRET-ALT-TWO', filename: 'secret-2.png', id: 901, mimeType: 'image/png' },
      ],
    },
  })
}

function exportCollection(w: ReturnType<typeof world>, body: unknown) {
  return w.endpoint(PATH)(makeRequest(w, USER, body))
}

describe('the export route is limited to the requesting user', () => {
  it('does not return alt text from a collection the caller cannot read', async () => {
    const w = world()
    const response = await exportCollection(w, { collection: 'secret' })
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('SECRET-ALT-ONE')).toBe(false)
    expect(response.ok && bodyText(body).includes('s1')).toBe(false)
  })

  it('does not return alt text from documents a scoped read rule excludes', async () => {
    const w = world({
      mediaRead: ({ req }: any) =>
        req.user?.role === 'admin' ? true : { owner: { equals: req.user.id } },
    })
    const response = await exportCollection(w, { collection: 'media' })
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('SOMEONE-ELSES-ALT')).toBe(false)
    expect(response.ok && bodyText(body).includes('m2')).toBe(false)
  })

  it('does not return a numeric document identifier from an inaccessible collection', async () => {
    const w = world()
    const response = await exportCollection(w, { collection: 'secret' })
    const body = await readJson(response)

    expect(response.ok && bodyText(body).includes('SECRET-ALT-TWO')).toBe(false)
  })
})
