/**
 * Legitimate use of the additional filter conveniences keeps working.
 */
import { describe, expect, it } from "vitest";
import { Custom } from "../../libs/providers/langchain-redis/src/filters.js";
import { StoredTag } from "../../libs/providers/langchain-redis/src/filter_stored.js";
import {
  createRecordingClient,
  expectSingleQuery,
  searchFluent,
} from "../helpers/query";

describe("plain-object filter shorthand", () => {
  it("renders tag, numeric and text fields", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, {
        tenant_id: "acme",
        price: { min: 90 },
        title: "javascript",
      })
    );
    expect(query).toContain(
      "@tenant_id:{acme} @price:[90 +inf] @title:(javascript)"
    );
  });

  it("renders an array of tag values with OR", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, { tenant_id: ["red", "blue"] })
    );
    expect(query).toContain("@tenant_id:{red|blue}");
  });

  it("renders a text value with spaces", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, { title: "wireless headphones" })
    );
    expect(query).toContain("@title:(wireless headphones)");
  });

  it("ignores fields that are not in the schema", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, { not_a_field: "ignored" })
    );
    expect(query.startsWith("* => [KNN")).toBe(true);
  });
});

describe("stored-value tag filter", () => {
  it("splits the stored value on the separator", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, StoredTag("tags", "red,blue"))
    );
    expect(query).toContain("@tags:{red|blue}");
  });

  it("honours a custom separator", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, StoredTag("tags", "red;blue", ";"))
    );
    expect(query).toContain("@tags:{red|blue}");
  });

  it("accepts several stored values", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, StoredTag("tags", ["red,blue", "green"]))
    );
    expect(query).toContain("@tags:{red|blue|green}");
  });
});

describe("custom query parameters", () => {
  it("substitutes an ordinary parameter value", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Custom("@tenant_id:{$tenant}", { tenant: "acme" }))
    );
    expect(query).toContain("@tenant_id:{acme}");
  });

  it("keeps raw custom query text unchanged", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Custom("@title:(wireless|bluetooth)"))
    );
    expect(query.startsWith("@title:(wireless|bluetooth) => [KNN")).toBe(true);
  });

  it("keeps raw custom query text with tag syntax unchanged", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchFluent(client, Custom("@tenant_id:{acme}"))
    );
    expect(query.startsWith("@tenant_id:{acme} => [KNN")).toBe(true);
  });
});
