/**
 * Test-side stand-in for Next.js's request cache.
 *
 * The product imports `unstable_cache` from 'next/cache.js'. Grading aliases that
 * specifier to this file, so the cache keeps one entry per key across requests,
 * exactly as the product's cache key defines it (and shares it the same way).
 */
type CacheEntry = { tags: string[]; value: unknown }

const store = new Map<string, CacheEntry>()

export function unstable_cache<T>(
  compute: () => Promise<T>,
  cacheKeyParts: string[],
  options: { revalidate?: number; tags?: string[] },
): () => Promise<T> {
  const key = JSON.stringify(cacheKeyParts)
  return async () => {
    if (!store.has(key)) {
      store.set(key, { tags: [...(options?.tags ?? [])], value: await compute() })
    }
    return store.get(key)!.value as T
  }
}

export function revalidateTag(tag: string, _profile?: string): void {
  for (const [key, entry] of store) {
    if (entry.tags.includes(tag)) store.delete(key)
  }
}

export function revalidatePath(): void {}

/** Test bookkeeping only: empty the cache between test cases. */
export function __resetCache(): void {
  store.clear()
}

/** Test bookkeeping only: the keys currently cached. */
export function __cacheKeys(): string[] {
  return [...store.keys()]
}
