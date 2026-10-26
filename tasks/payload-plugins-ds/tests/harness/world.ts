/**
 * Test-side stand-in for the Payload host application.
 *
 * The plugin is constructed with the same `payloadAltTextPlugin(config)(config)`
 * call a host application makes, and its registered handlers are invoked with a
 * request object shaped like Payload's. The fake Local API applies the same
 * access rule Payload applies: an omitted `overrideAccess` acts as `true`
 * (elevated), while `overrideAccess: false` evaluates the collection's own
 * `read`/`update` access and throws `Forbidden` (or filters by the returned
 * `where`) exactly as Payload's Local API does.
 */
import { payloadAltTextPlugin } from '../../alt-text/src/plugin.ts'

export const GENERATED_ALT = 'GENERATED-ALT-TEXT'
export const GENERATED_KEYWORDS = ['generated', 'keyword']
export const IMPORTED_ALT = 'IMPORTED-ALT-TEXT'

export const ADMIN = { email: 'admin@example.test', id: 'admin-1', role: 'admin' }
export const USER = { email: 'user@example.test', id: 'user-1', role: 'user' }

export class ForbiddenError extends Error {
  status = 403
  constructor() {
    super('Forbidden')
  }
}

type Doc = Record<string, any>
type AccessFn = (args: { req: any; id?: unknown; data?: unknown }) => unknown
export type CollectionSpec = {
  slug: string
  access?: { create?: AccessFn; read?: AccessFn; update?: AccessFn }
}

function matchesWhere(doc: Doc, where: any): boolean {
  if (!where) return true
  if (Array.isArray(where)) return where.every((clause) => matchesWhere(doc, clause))
  if (Array.isArray(where.or)) return where.or.some((clause: any) => matchesWhere(doc, clause))
  if (Array.isArray(where.and)) return where.and.every((clause: any) => matchesWhere(doc, clause))
  for (const [field, condition] of Object.entries<any>(where)) {
    const value = doc[field]
    if (condition && typeof condition === 'object' && !Array.isArray(condition)) {
      if ('equals' in condition && value !== condition.equals) return false
      if ('in' in condition && !(condition.in as unknown[]).includes(value)) return false
      if ('like' in condition) {
        if (typeof value !== 'string' || !value.includes(condition.like)) return false
      }
      if ('exists' in condition) {
        const present = value !== undefined && value !== null
        if (Boolean(condition.exists) !== present) return false
      }
    } else if (value !== condition) {
      return false
    }
  }
  return true
}

export type BuildOptions = {
  collections: CollectionSpec[]
  docs?: Record<string, Doc[]>
  failFind?: string[]
  localized?: boolean
  altText?: string
  bulkAltText?: string
}

export function buildWorld(options: BuildOptions) {
  const docs = options.docs ?? {}
  const failFind = new Set(options.failFind ?? [])
  const writers: { collection: string; data: Doc; id: unknown; locale?: string }[] = []
  const calls: { method: string; collection: string; id?: unknown; overrideAccess?: boolean }[] = []

  const baseConfig: any = {
    admin: { dashboard: { widgets: [] } },
    collections: options.collections.map((spec) => ({
      slug: spec.slug,
      upload: true,
      access: spec.access,
      fields: [],
      hooks: {},
      admin: {},
    })),
    custom: {},
    endpoints: [],
    i18n: {},
    localization: options.localized
      ? {
          localeCodes: ['en', 'de'],
          locales: [
            { code: 'en', label: 'English' },
            { code: 'de', label: 'German' },
          ],
        }
      : undefined,
  }

  const resolver = {
    key: 'test-resolver',
    resolve: async () => ({
      success: true,
      result: {
        altText: options.altText ?? GENERATED_ALT,
        keywords: GENERATED_KEYWORDS,
      },
    }),
    resolveBulk: async ({ locales }: { locales: string[] }) => ({
      success: true,
      results: Object.fromEntries(
        locales.map((locale) => [
          locale,
          { altText: options.bulkAltText ?? GENERATED_ALT, keywords: GENERATED_KEYWORDS },
        ]),
      ),
    }),
  }

  const pluginOutput = payloadAltTextPlugin({
    collections: options.collections.map((spec) => spec.slug),
    getImageThumbnail: () => 'https://example.test/thumb.png',
    locale: 'en',
    resolver,
  } as any)(baseConfig)

  const collectionConfig = (slug: string) =>
    (pluginOutput.collections as any[]).find((entry) => entry.slug === slug)

  const runAccess = async (
    slug: string,
    verb: 'read' | 'update',
    args: { user: any; id?: unknown; data?: unknown },
  ): Promise<unknown> => {
    const fn = collectionConfig(slug)?.access?.[verb]
    if (typeof fn !== 'function') {
      return true
    }
    try {
      return await fn({ req: { payload, user: args.user }, id: args.id, data: args.data })
    } catch {
      throw new ForbiddenError()
    }
  }

  const payload: any = {
    collections: Object.fromEntries(
      (pluginOutput.collections as any[]).map((entry) => [
        entry.slug,
        { config: entry },
      ]),
    ),
    config: pluginOutput,
    logger: { debug() {}, error() {}, info() {}, warn() {} },

    async find(args: any) {
      calls.push({
        collection: args.collection,
        method: 'find',
        overrideAccess: args.overrideAccess,
      })
      let found = [...(docs[args.collection] ?? [])]
      if (args.overrideAccess === false) {
        const constraint = await runAccess(args.collection, 'read', { user: args.user })
        if (constraint === false) throw new ForbiddenError()
        if (constraint && typeof constraint === 'object') {
          found = found.filter((doc) => matchesWhere(doc, constraint))
        }
      } else if (failFind.has(args.collection)) {
        throw new Error('database unavailable')
      }
      found = found.filter((doc) => matchesWhere(doc, args.where))
      return {
        docs: found,
        hasNextPage: false,
        totalDocs: found.length,
      }
    },

    async findByID(args: any) {
      calls.push({
        collection: args.collection,
        id: args.id,
        method: 'findByID',
        overrideAccess: args.overrideAccess,
      })
      const doc = (docs[args.collection] ?? []).find((entry) => entry.id === args.id)
      if (args.overrideAccess === false) {
        const constraint = await runAccess(args.collection, 'read', {
          id: args.id,
          user: args.user,
        })
        if (constraint === false) throw new ForbiddenError()
        if (constraint && typeof constraint === 'object') {
          if (!doc || !matchesWhere(doc, constraint)) return null
        }
      }
      return doc ?? null
    },

    async update(args: any) {
      calls.push({
        collection: args.collection,
        id: args.id,
        method: 'update',
        overrideAccess: args.overrideAccess,
      })
      if (args.overrideAccess === false) {
        const constraint = await runAccess(args.collection, 'update', {
          data: args.data,
          id: args.id,
          user: args.user,
        })
        if (constraint === false) throw new ForbiddenError()
        if (constraint && typeof constraint === 'object') {
          const doc = (docs[args.collection] ?? []).find((entry) => entry.id === args.id)
          if (!doc || !matchesWhere(doc, constraint)) throw new ForbiddenError()
        }
      }
      writers.push({
        collection: args.collection,
        data: args.data,
        id: args.id,
        locale: args.locale,
      })
      return { id: args.id, ...args.data }
    },
  }

  return {
    calls,
    endpoint(path: string) {
      const entry = (pluginOutput.endpoints as any[]).find((candidate) => candidate.path === path)
      if (!entry) throw new Error(`endpoint not registered: ${path}`)
      return entry.handler
    },
    pluginOutput,
    payload,
    writesTo(collection: string) {
      return writers.filter((write) => write.collection === collection)
    },
    writers,
  }
}

export type World = ReturnType<typeof buildWorld>

export function makeRequest(world: World, user: any, body?: unknown) {
  return {
    context: {},
    json: async () => body,
    locale: 'en',
    payload: world.payload,
    t: (key: string) => key,
    user,
  } as any
}

/** Small helper: the response is required to exist and to be readable as JSON. */
export async function readJson(response: any): Promise<any> {
  if (!response || typeof response.json !== 'function') {
    throw new Error('the handler did not return a response')
  }
  return response.json()
}

export function bodyText(body: unknown): string {
  return JSON.stringify(body ?? null)
}
