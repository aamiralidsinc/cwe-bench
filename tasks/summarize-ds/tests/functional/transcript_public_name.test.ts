import { describe, expect, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  FEED_URL,
  PUBLIC,
  TRANSCRIPT_MARKER,
  VTT_BODY,
  called,
  feedXml,
  makeFetch,
  rss,
  vtt,
} from "../helpers.js";

describe("legitimate podcast transcripts", () => {
  it("fetches a transcript from a public host name and returns its text", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(rss(`<podcast:transcript url="${PUBLIC.transcriptName}" type="text/vtt"/>`)),
      [PUBLIC.transcriptName]: () => vtt(VTT_BODY(TRANSCRIPT_MARKER)),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    const out = await client.fetchLinkContent(FEED_URL);

    expect(called(stub, PUBLIC.transcriptName)).toBe(true);
    expect(out.content).toContain(TRANSCRIPT_MARKER);
  });
});
