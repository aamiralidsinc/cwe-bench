/**
 * A custom query may be raw text chosen by the caller, but the values a caller
 * binds into it are data and must stay data.
 */
import { describe, it } from "vitest";
import { Custom } from "../../libs/providers/langchain-redis/src/filters.js";
import {
  QUERY_BREAKOUT,
  createRecordingClient,
  expectBlocked,
  searchFluent,
} from "../helpers/query";

describe("custom query parameter values are data", () => {
  it("a bound tag value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Custom("@tenant_id:{$tenant}", { tenant: QUERY_BREAKOUT })
    );
    expectBlocked(captured);
  });

  it("a bound text value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Custom("@title:($query)", { query: "acme) => [KNN 1 @content_vector $vector AS vector_score] @tenant_scope:(leaked" })
    );
    expectBlocked(captured);
  });

  it("a bound numeric value cannot contribute a second query", async () => {
    const client = createRecordingClient();
    const captured = await searchFluent(
      client,
      Custom("@price:[$minimum 100]", {
        minimum: "1] => [KNN 1 @content_vector $vector AS vector_score] @tenant_scope:[0 0",
      })
    );
    expectBlocked(captured);
  });
});
