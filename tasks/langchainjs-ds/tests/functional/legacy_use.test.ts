/**
 * Legitimate use of the deprecated store keeps working exactly as today.
 */
import { describe, expect, it } from "vitest";
import {
  createRecordingClient,
  expectSingleQuery,
  searchLegacy,
  searchLegacyMetadata,
} from "../helpers/query";

describe("legitimate legacy-store filtering", () => {
  it("ORs the values of a string-array filter", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(await searchLegacy(client, ["foo", "bar"]));
    expect(query).toContain("@metadata:(foo|bar)");
  });

  it("passes an explicitly raw filter string through unchanged", async () => {
    const client = createRecordingClient();
    const raw = "@metadata:(foo|bar) @metadata.title:(baz)";
    const query = expectSingleQuery(await searchLegacy(client, raw));
    expect(query).toContain(raw);
  });

  it("filters on a structured tag value", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchLegacyMetadata(client, { tenant_id: "acme" })
    );
    expect(query).toContain("@metadata.tenant_id:{acme}");
  });

  it("filters on structured tag values with OR", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchLegacyMetadata(client, { tenant_id: ["red", "blue"] })
    );
    expect(query).toContain("@metadata.tenant_id:({red}|{blue})");
  });

  it("filters on a structured text value with spaces", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchLegacyMetadata(client, { title: "javascript tutorial" })
    );
    expect(query).toContain("@metadata.title:(javascript tutorial)");
  });

  it("filters on a structured numeric range", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchLegacyMetadata(client, { price: { min: 90 } })
    );
    expect(query).toContain("@metadata.price:[90 +inf]");
  });

  it("filters on a structured numeric value", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchLegacyMetadata(client, { price: 42 })
    );
    expect(query).toContain("@metadata.price:[42 42]");
  });

  it("ignores a field that is not in the schema", async () => {
    const client = createRecordingClient();
    const query = expectSingleQuery(
      await searchLegacyMetadata(client, { not_a_field: "ignored" })
    );
    expect(query.startsWith("* => [KNN")).toBe(true);
  });
});
