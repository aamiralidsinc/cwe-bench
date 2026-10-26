/**
 * Shared helpers for the hidden suites.
 *
 * The tests drive the vector stores' public search entry point with a
 * recording Redis client, so they observe exactly what the library would send
 * to RediSearch. Nothing here imports a safety helper from the product: the
 * expected outcomes are computed in the tests themselves.
 */
import { expect, vi } from "vitest";
import { FakeEmbeddings } from "@langchain/core/utils/testing";
import { SchemaFieldTypes } from "redis";
import { FluentRedisVectorStore } from "../../libs/providers/langchain-redis/src/vectorstores_fluent.js";
import { RedisVectorStore } from "../../libs/providers/langchain-redis/src/vectorstores.js";

export const SENTINEL_FIELD = "tenant_scope";

/** A value that tries to close the current filter and open a second query. */
export const QUERY_BREAKOUT =
  "acme} => [KNN 1 @content_vector $vector AS vector_score] @tenant_scope:{leaked";

/** The same attempt shaped for a parenthesised (text) clause. */
export const TEXT_BREAKOUT =
  "acme) => [KNN 1 @content_vector $vector AS vector_score] @tenant_scope:(leaked";

/** The same attempt shaped for a bracketed numeric/geo range. */
export const RANGE_BREAKOUT =
  "1 2] => [KNN 1 @content_vector $vector AS vector_score] @tenant_scope:[0 0";

/** The same attempt shaped for a bare field name. */
export const FIELD_BREAKOUT = QUERY_BREAKOUT.replace(/^acme/, "tenant_id");

export const FLUENT_SCHEMA = [
  { name: "tenant_id", type: "tag" as const },
  { name: "category", type: "tag" as const },
  { name: "tags", type: "tag" as const },
  { name: "title", type: "text" as const },
  { name: "description", type: "text" as const },
  { name: "price", type: "numeric" as const },
  { name: "created_at", type: "numeric" as const },
  { name: "location", type: "geo" as const },
];

export const LEGACY_SCHEMA = {
  tenant_id: { type: SchemaFieldTypes.TAG },
  category: { type: SchemaFieldTypes.TAG },
  tags: { type: SchemaFieldTypes.TAG },
  title: { type: SchemaFieldTypes.TEXT },
  description: { type: SchemaFieldTypes.TEXT },
  price: { type: SchemaFieldTypes.NUMERIC },
  created_at: { type: SchemaFieldTypes.NUMERIC },
  location: { type: SchemaFieldTypes.GEO },
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AnyClient = any;

/** A Redis client that records the FT.SEARCH arguments and returns no documents. */
export function createRecordingClient(): AnyClient {
  return {
    ft: {
      info: vi.fn().mockResolvedValue({ numDocs: 0, attributes: [] }),
      create: vi.fn().mockResolvedValue(undefined),
      search: vi.fn().mockResolvedValue({ total: 0, documents: [] }),
      dropIndex: vi.fn().mockResolvedValue(undefined),
    },
    hSet: vi.fn(),
    expire: vi.fn(),
    del: vi.fn(),
    multi: vi.fn().mockImplementation(() => ({
      exec: vi.fn(),
      hSet: vi.fn(),
      expire: vi.fn(),
    })),
  };
}

export function makeFluentStore(
  client: AnyClient,
  schema: unknown = FLUENT_SCHEMA,
  extra: Record<string, unknown> = {}
): FluentRedisVectorStore {
  return new FluentRedisVectorStore(new FakeEmbeddings(), {
    redisClient: client,
    indexName: "hidden-test",
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    customSchema: schema as any,
    ...extra,
  } as never);
}

export function makeLegacyStore(
  client: AnyClient,
  schema: unknown = LEGACY_SCHEMA
): RedisVectorStore {
  return new RedisVectorStore(new FakeEmbeddings(), {
    redisClient: client,
    indexName: "hidden-test",
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    customSchema: schema as any,
  });
}

export interface Captured {
  /** Every query string the store passed to FT.SEARCH. */
  queries: string[];
  /** The error the search raised, if it raised one. */
  error: unknown;
}

async function capture(
  run: () => Promise<unknown>,
  client: AnyClient
): Promise<Captured> {
  let error: unknown = null;
  try {
    await run();
  } catch (caught) {
    error = caught;
  }
  const queries: string[] = client.ft.search.mock.calls.map((call: unknown[]) =>
    String(call[1] ?? "")
  );
  return { queries, error };
}

export function searchFluent(
  client: AnyClient,
  filter: unknown,
  k = 5
): Promise<Captured> {
  const store = makeFluentStore(client);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return capture(() => store.similaritySearch("probe", k, filter as any), client);
}

/** Runs a search on an already-configured store (e.g. with a default filter). */
export function searchOn(
  client: AnyClient,
  store: FluentRedisVectorStore,
  filter?: unknown,
  k = 5
): Promise<Captured> {
  return capture(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    () => store.similaritySearch("probe", k, filter as any),
    client
  );
}

export function searchLegacy(
  client: AnyClient,
  filter: unknown,
  k = 5
): Promise<Captured> {
  const store = makeLegacyStore(client);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return capture(() => store.similaritySearch("probe", k, filter as any), client);
}

/** Drives the legacy store's structured metadata-filter search path. */
export function searchLegacyMetadata(
  client: AnyClient,
  metadataFilter: Record<string, unknown>,
  k = 5
): Promise<Captured> {
  const store = makeLegacyStore(client);
  return capture(
    () =>
      store.similaritySearchVectorWithScoreAndMetadata(
        [0.1, 0.2, 0.3, 0.4],
        k,
        metadataFilter
      ),
    client
  );
}

/** Number of occurrences of `token` whose first character is not backslash-escaped. */
export function countUnescaped(text: string, token: string): number {
  let count = 0;
  let from = 0;
  for (;;) {
    const index = text.indexOf(token, from);
    if (index === -1) {
      return count;
    }
    from = index + token.length;
    let slashes = 0;
    for (let i = index - 1; i >= 0 && text[i] === "\\"; i -= 1) {
      slashes += 1;
    }
    if (slashes % 2 === 0) {
      count += 1;
    }
  }
}

/**
 * True when the query contains a field modifier (`@name:` with an unescaped
 * colon) for `field`, i.e. the injected text became live query syntax.
 */
export function hasLiveFieldReference(query: string, field: string): boolean {
  const needle = `@${field}`;
  let from = 0;
  for (;;) {
    const index = query.indexOf(needle, from);
    if (index === -1) {
      return false;
    }
    from = index + needle.length;
    let slashes = 0;
    for (let i = index - 1; i >= 0 && query[i] === "\\"; i -= 1) {
      slashes += 1;
    }
    if (slashes % 2 === 1) {
      continue; // the modifier's '@' is escaped
    }
    let cursor = index + needle.length;
    while (cursor < query.length && /\s/.test(query[cursor])) {
      cursor += 1;
    }
    let colonSlashes = 0;
    while (cursor < query.length && query[cursor] === "\\") {
      colonSlashes += 1;
      cursor += 1;
    }
    if (
      colonSlashes % 2 === 0 &&
      cursor < query.length &&
      query[cursor] === ":"
    ) {
      return true;
    }
  }
}

/**
 * Asserts an attempted injection did not reach the search engine as syntax:
 * either the search failed before any query was sent, or the sent query keeps
 * exactly the one vector clause the store appends and no live field modifier
 * for the sentinel field.
 */
export function expectBlocked(captured: Captured): void {
  if (captured.error) {
    // The refusal must happen before the query is executed.
    expect(captured.queries).toHaveLength(0);
    return;
  }
  expect(captured.queries.length).toBeGreaterThan(0);
  for (const query of captured.queries) {
    expect(countUnescaped(query, "=>")).toBe(1);
    expect(hasLiveFieldReference(query, SENTINEL_FIELD)).toBe(false);
  }
}

/** Asserts a legitimate search ran and kept exactly one vector clause. */
export function expectSingleQuery(captured: Captured): string {
  expect(captured.error).toBeNull();
  expect(captured.queries).toHaveLength(1);
  expect(countUnescaped(captured.queries[0], "=>")).toBe(1);
  return captured.queries[0];
}
