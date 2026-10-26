/**
 * The plain-object filter shorthand is another way for a caller to supply a
 * metadata filter; its values must stay data like any other filter's.
 */
import { describe, it } from "vitest";
import {
  QUERY_BREAKOUT,
  RANGE_BREAKOUT,
  TEXT_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchFluent,
} from "../helpers/query";

describe("plain-object filter values are data", () => {
  it("a tag value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, {
      tenant_id: QUERY_BREAKOUT,
    });
    expectBlocked(captured);
  });

  it("an array of tag values cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, {
      tenant_id: ["acme", QUERY_BREAKOUT],
    });
    expectBlocked(captured);
  });

  it("a text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, {
      title: TEXT_BREAKOUT,
    });
    expectBlocked(captured);
  });

  it("a numeric value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, {
      price: RANGE_BREAKOUT,
    });
    expectBlocked(captured);
  });

  it("a numeric range bound cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, {
      price: { min: RANGE_BREAKOUT, max: 100 },
    });
    expectBlocked(captured);
  });
});
