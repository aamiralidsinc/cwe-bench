import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  FEED_URL,
  INTERNAL,
  VTT_BODY,
  expectNoNonPublicFetch,
  feedXml,
  makeFetch,
  rss,
  vtt,
} from "../helpers.js";

describe("feed-declared transcript destinations", () => {
  it("does not fetch a transcript on a host name that resolves to loopback", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(rss(`<podcast:transcript url="${INTERNAL.privateName}" type="text/vtt"/>`)),
      [INTERNAL.privateName]: () => vtt(VTT_BODY("internal-transcript")),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    await client.fetchLinkContent(FEED_URL).catch(() => undefined);

    expectNoNonPublicFetch(stub);
  });
});
