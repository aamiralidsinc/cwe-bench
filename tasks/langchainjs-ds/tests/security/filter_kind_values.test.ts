/**
 * Every filter kind that carries a caller value must keep that value inert,
 * including the numeric, date/time and geographic kinds.
 */
import { describe, it } from "vitest";
import {
  Geo,
  Num,
  Timestamp,
} from "../../libs/providers/langchain-redis/src/filters.js";
import {
  RANGE_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchFluent,
} from "../helpers/query";

describe("numeric, date/time and geographic values are data", () => {
  it("an equality bound cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      // The value is supplied by data at run time, not by a typed caller.
      client,
      Num("price").eq(RANGE_BREAKOUT as unknown as number)
    );
    expectBlocked(captured);
  });

  it("a comparison bound cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Num("price").gt(RANGE_BREAKOUT as unknown as number)
    );
    expectBlocked(captured);
  });

  it("a range bound cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Num("price").between(
        RANGE_BREAKOUT as unknown as number,
        100
      )
    );
    expectBlocked(captured);
  });

  it("a date/time bound cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Timestamp("created_at").gte(RANGE_BREAKOUT as unknown as number)
    );
    expectBlocked(captured);
  });

  it("a geographic radius cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Geo("location").within(1, 2, RANGE_BREAKOUT as unknown as number, "km")
    );
    expectBlocked(captured);
  });
});
