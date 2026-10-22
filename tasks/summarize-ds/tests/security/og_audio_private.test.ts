import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import { FEED_URL, expectNoNonPublicFetch, feedXml, makeFetch, rss } from "../helpers.js";

describe("feed-declared audio destinations", () => {
  it("does not fetch audio named by feed metadata on a loopback address", async () => {
    const audioUrl = "http://127.0.0.1:9/internal/og-audio.mp3";
    const stub = makeFetch({
      [FEED_URL]: () => feedXml(rss(`<meta property="og:audio" content="${audioUrl}"/>`)),
      [audioUrl]: () =>
        new Response(new Uint8Array(1024), {
          status: 200,
          headers: { "content-type": "audio/mpeg", "content-length": "1024" },
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
