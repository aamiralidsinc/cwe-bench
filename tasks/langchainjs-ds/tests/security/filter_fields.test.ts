/**
 * The field a filter addresses is also a name, not syntax. A name that carries
 * clause syntax may not add a query or redirect the condition.
 */
import { describe, it } from "vitest";
import {
  Geo,
  Num,
  Tag,
  Text,
  Timestamp,
} from "../../libs/providers/langchain-redis/src/filters.js";
import {
  FIELD_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchFluent,
} from "../helpers/query";

const FIELD = FIELD_BREAKOUT; // closes the current clause and opens another

describe("filter field names are names", () => {
  it("a tag field name cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, Tag(FIELD).eq("acme"));
    expectBlocked(captured);
  });

  it("a numeric field name cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, Num(FIELD).eq(10));
    expectBlocked(captured);
  });

  it("a text field name cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, Text(FIELD).eq("acme"));
    expectBlocked(captured);
  });

  it("a geographic field name cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Geo(FIELD).within(-122.4, 37.7, 10, "km")
    );
    expectBlocked(captured);
  });

  it("a date/time field name cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(client, Timestamp(FIELD).gt(1672531200));
    expectBlocked(captured);
  });
});
