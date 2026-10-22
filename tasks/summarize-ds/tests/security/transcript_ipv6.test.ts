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
  it("does not fetch a transcript on an IPv6 unique-local address", async () => {
    const stub = makeFetch({
      [FEED_URL]: () => feedXml(rss(`<podcast:transcript url="${INTERNAL.ula}" type="text/vtt"/>`)),
      [INTERNAL.ula]: () => vtt(VTT_BODY("internal-transcript")),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    await client.fetchLinkContent(FEED_URL).catch(() => undefined);

    expectNoNonPublicFetch(stub);
  });
});
