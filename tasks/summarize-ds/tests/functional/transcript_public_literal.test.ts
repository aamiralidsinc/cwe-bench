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
  it("fetches a transcript from a public IP literal and returns its text", async () => {
    const stub = makeFetch({
      [FEED_URL]: () =>
        feedXml(rss(`<podcast:transcript url="${PUBLIC.transcriptLiteral}" type="text/vtt"/>`)),
      [PUBLIC.transcriptLiteral]: () => vtt(VTT_BODY(TRANSCRIPT_MARKER)),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    const out = await client.fetchLinkContent(FEED_URL);

    expect(called(stub, PUBLIC.transcriptLiteral)).toBe(true);
    expect(out.content).toContain(TRANSCRIPT_MARKER);
  });
});
