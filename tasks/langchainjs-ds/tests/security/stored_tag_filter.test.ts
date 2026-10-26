/**
 * The stored-value tag filter splits values on the field's separator; the
 * pieces are still caller data and may not become query syntax.
 */
import { describe, it } from "vitest";
import { StoredTag } from "../../libs/providers/langchain-redis/src/filter_stored.js";
import {
  QUERY_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchFluent,
} from "../helpers/query";

describe("stored-value tag filter values are data", () => {
  it("a separated value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      StoredTag("tags", `acme,${QUERY_BREAKOUT}`)
    );
    expectBlocked(captured);
  });

  it("an array of separated values cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      StoredTag("tags", ["acme", QUERY_BREAKOUT])
    );
    expectBlocked(captured);
  });

  it("a custom separator cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      StoredTag("tags", `acme;${QUERY_BREAKOUT}`, ";")
    );
    expectBlocked(captured);
  });

  it("a field name cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      StoredTag(`${QUERY_BREAKOUT}`, "acme")
    );
    expectBlocked(captured);
  });
});
