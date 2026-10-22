import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  FEED_URL,
  INTERNAL,
  expectNoNonPublicFetch,
  feedXml,
  json,
  makeFetch,
  rss,
} from "../helpers.js";

describe("feed-declared chapter destinations", () => {
  it("does not fetch chapter metadata on a loopback address", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(
          rss(
            `<podcast:chapters url="${INTERNAL.chapters}" type="application/json+chapters"/>`,
          ),
        ),
      [INTERNAL.chapters]: () => json({ chapters: [{ title: "Internal chapter" }] }),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    await client.fetchLinkContent(FEED_URL).catch(() => undefined);

    expectNoNonPublicFetch(stub);
  });
});
