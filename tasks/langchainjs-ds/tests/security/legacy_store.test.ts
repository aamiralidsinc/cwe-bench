/**
 * The deprecated store builds its own query string. Every value a caller puts
 * into its filter must stay data there as well.
 */
import { describe, it } from "vitest";
import {
  QUERY_BREAKOUT,
  RANGE_BREAKOUT,
  TEXT_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchLegacy,
  searchLegacyMetadata,
} from "../helpers/query";

describe("legacy store filter values are data", () => {
  it("a structured tag value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchLegacyMetadata(client, {
      tenant_id: QUERY_BREAKOUT,
    });
    expectBlocked(captured);
  });

  it("a structured array of tag values cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchLegacyMetadata(client, {
      tenant_id: ["acme", QUERY_BREAKOUT],
    });
    expectBlocked(captured);
  });

  it("a structured text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchLegacyMetadata(client, {
      title: TEXT_BREAKOUT,
    });
    expectBlocked(captured);
  });

  it("a structured numeric value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchLegacyMetadata(client, {
      price: RANGE_BREAKOUT,
    });
    expectBlocked(captured);
  });

  it("a structured numeric range cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchLegacyMetadata(client, {
      price: { min: RANGE_BREAKOUT, max: 100 },
    });
    expectBlocked(captured);
  });

  it("a string-array filter value cannot restructure the query", async () => {
    const client = createRecordingClient();
    const captured = await searchLegacy(client, [
      "acme) => [KNN 1 @content_vector $vector AS vector_score] @metadata:(leaked",
    ]);
    expectBlocked(captured);
  });
});
