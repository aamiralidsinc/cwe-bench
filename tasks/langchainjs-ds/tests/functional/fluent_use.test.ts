/**
 * Legitimate filtering keeps working exactly as today.
 */
import { describe, expect, it } from "vitest";
import {
  Geo,
  Num,
  Tag,
  Text,
  Timestamp,
} from "../../libs/providers/langchain-redis/src/filters.js";
import {
  FLUENT_SCHEMA,
  createRecordingClient,
  expectSingleQuery,
  makeFluentStore,
  searchFluent,
  searchOn,
} from "../helpers/query";

describe("legitimate fluent filtering", () => {
  it("filters on one tag value", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Tag("tenant_id").eq("acme"))
    );
    expect(query).toContain("@tenant_id:{acme}");
  });

  it("filters on several tag values with OR", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Tag("tenant_id").eq(["red", "blue"]))
    );
    expect(query).toContain("@tenant_id:{red|blue}");
  });

  it("filters on a set of tag values", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Tag("tenant_id").eq(new Set(["red", "blue"])))
    );
    expect(query).toContain("@tenant_id:{red|blue}");
  });

  it("filters on a negated tag value", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Tag("tenant_id").ne("archived"))
    );
    expect(query).toContain("(-@tenant_id:{archived})");
  });

  it("keeps punctuation in a tag value matching", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Tag("tenant_id").eq("tenant-42:prod"))
    );
    // The value is still carried in the tag clause; how it is safe-encoded is
    // the fix's choice, so the assertion is structural.
    expect(query.startsWith("@tenant_id:{")).toBe(true);
    expect(query.split("@tenant_id:{")).toHaveLength(2);
    expect(query).toContain("tenant");
    expect(query).toContain("prod");
  });

  it("keeps an exact text phrase with spaces", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Text("title").eq("wireless headphones"))
    );
    expect(query).toContain('@title:("wireless headphones")');
  });

  it("keeps tokenised text matching with spaces", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Text("description").match("wireless bluetooth"))
    );
    expect(query).toContain("@description:(wireless bluetooth)");
  });

  it("keeps wildcard operators in a wildcard search", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Text("title").wildcard("*phone?"))
    );
    expect(query).toContain("@title:(*phone?)");
  });

  it("keeps fuzzy matching", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Text("title").fuzzy("headphone"))
    );
    expect(query).toContain("@title:(%%headphone%%)");
  });

  it("keeps numeric comparisons", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Num("price").between(10, 20))
    );
    expect(query).toContain("@price:[10 20]");
  });

  it("keeps exclusive numeric bounds", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(await searchFluent(client, Num("price").gt(50)));
    expect(query).toContain("@price:[(50 +inf]");
  });

  it("keeps date/time bounds", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(
        client,
        Timestamp("created_at").eq(new Date("2023-01-01T00:00:00Z"))
      )
    );
    expect(query).toContain("@created_at:[1672531200 1672531200]");
  });

  it("keeps geographic filters", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Geo("location").within(-122.4194, 37.7749, 10, "km"))
    );
    expect(query).toContain("@location:[-122.4194 37.7749 10 km]");
  });

  it("keeps an empty filter as a wildcard", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Tag("tenant_id").eq([]))
    );
    expect(query.startsWith("* => [KNN")).toBe(true);
  });

  it("keeps combined filters working", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(
        client,
        Tag("category").eq("books").and(Num("price").lt(30))
      )
    );
    expect(query).toContain("@category:{books} @price:[-inf (30]");
  });

  it("keeps a configured default filter working", async () => {
    const client = createRecordingClient();
    const store = makeFluentStore(client, FLUENT_SCHEMA, {
      filter: Tag("tenant_id").eq("acme"),
    });
    const captured = await searchOn(client, store);
    expect(captured.error).toBeNull();
    expect(captured.queries).toHaveLength(1);
    expect(captured.queries[0]).toContain("@tenant_id:{acme}");
  });
});
