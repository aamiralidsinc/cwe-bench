import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  FEED_URL,
  INTERNAL,
  expectNoNonPublicFetch,
  feedXml,
  makeFetch,
  rss,
} from "../helpers.js";

describe("feed-declared enclosure destinations", () => {
  it("does not probe or download episode media on a private address", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(rss(`<enclosure url="${INTERNAL.privateTen}" type="audio/mpeg"/>`)),
      [INTERNAL.privateTen]: () =>
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

    expectNoNonPublicFetch(stub);
  });
});
