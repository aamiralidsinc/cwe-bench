import { describe, expect, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  FEED_URL,
  PUBLIC,
  called,
  expectNoNonPublicFetch,
  feedXml,
  makeFetch,
  rss,
} from "../helpers.js";

describe("legitimate feed enclosure media", () => {
  it("still probes episode media on a public address", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(rss(`<enclosure url="${PUBLIC.enclosure}" type="audio/mpeg"/>`)),
      [PUBLIC.enclosure]: () =>
        new Response(null, {
          status: 200,
          headers: {
            "content-length": String(2 * 1024 * 1024 * 1024),
            "content-type": "audio/mpeg",
          },
        }),
    });
    const client = createLinkPreviewClient({
      fetch: stub.impl,
      env: {},
      openaiApiKey: "verifier-test-key",
    });

    await client.fetchLinkContent(FEED_URL).catch(() => undefined);

    expect(called(stub, PUBLIC.enclosure)).toBe(true);
    expectNoNonPublicFetch(stub);
  });
});
