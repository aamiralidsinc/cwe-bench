/**
 * A metadata filter value must stay data: it may not close the current clause
 * and contribute a second query. Driven through the public search entry point.
 */
import { describe, expect, it } from "vitest";
import {
  Tag,
  Text,
} from "../../libs/providers/langchain-redis/src/filters.js";
import {
  QUERY_BREAKOUT,
  TEXT_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchFluent,
} from "../helpers/query";

describe("filter values are data", () => {
  it("a single tag value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Tag("tenant_id").eq(QUERY_BREAKOUT)
    );
    expectBlocked(captured);
  });

  it("an array of tag values cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Tag("tenant_id").eq(["acme", QUERY_BREAKOUT])
    );
    expectBlocked(captured);
  });

  it("a set of tag values cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Tag("tenant_id").eq(new Set(["acme", QUERY_BREAKOUT]))
    );
    expectBlocked(captured);
  });

  it("a negated tag value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Tag("tenant_id").ne(QUERY_BREAKOUT)
    );
    expectBlocked(captured);
  });

  it("an exact text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Text("title").eq(TEXT_BREAKOUT)
    );
    expectBlocked(captured);
  });

  it("a tokenised text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Text("description").match(TEXT_BREAKOUT)
    );
    expectBlocked(captured);
  });

  it("a wildcard text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Text("title").wildcard(TEXT_BREAKOUT)
    );
    expectBlocked(captured);
  });

  it("a fuzzy text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Text("title").fuzzy(TEXT_BREAKOUT)
    );
    expectBlocked(captured);
  });

  it("a value cannot add a clause through a combined filter", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Tag("category").eq("books").and(Text("title").eq(TEXT_BREAKOUT))
    );
    expectBlocked(captured);
  });
});
