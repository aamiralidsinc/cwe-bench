import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  FEED_URL,
  INTERNAL,
  VTT_BODY,
  expectNoNonPublicFetch,
  feedXml,
  makeFetch,
  redirectTo,
  rss,
  vtt,
} from "../helpers.js";

describe("feed-declared transcript destinations", () => {
  it("does not follow a public redirect into a link-local metadata address", async () => {
    const firstHop = "https://cdn.summarize-test.example/redirecting-transcript.vtt";
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(rss(`<podcast:transcript url="${firstHop}" type="text/vtt"/>`)),
      [firstHop]: () => redirectTo(INTERNAL.metadata),
      [INTERNAL.metadata]: () => vtt(VTT_BODY("internal-transcript")),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    await client.fetchLinkContent(FEED_URL).catch(() => undefined);

    expectNoNonPublicFetch(stub);
  });
});
