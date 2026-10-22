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

describe("legitimate feed chapter metadata", () => {
  it("still fetches chapter metadata from a public address", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(
          rss(`<podcast:chapters url="${PUBLIC.chapters}" type="application/json+chapters"/>`),
        ),
      [PUBLIC.chapters]: () =>
        new Response(
          JSON.stringify({ chapters: [{ title: "Public chapter", startTime: 0 }] }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    await client.fetchLinkContent(FEED_URL).catch(() => undefined);

    expect(called(stub, PUBLIC.chapters)).toBe(true);
    expectNoNonPublicFetch(stub);
  });
});
