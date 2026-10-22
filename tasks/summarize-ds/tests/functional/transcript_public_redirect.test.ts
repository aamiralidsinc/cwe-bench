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
  redirectTo,
  rss,
  vtt,
} from "../helpers.js";

describe("legitimate podcast transcripts", () => {
  it("follows a redirect that stays on public destinations and returns the text", async () => {
    const firstHop = "https://cdn.summarize-test.example/redirecting-transcript.vtt";
    const stub = makeFetch({
      [FEED_URL]: () => feedXml(rss(`<podcast:transcript url="${firstHop}" type="text/vtt"/>`)),
      [firstHop]: () => redirectTo(PUBLIC.transcriptSecondHop),
      [PUBLIC.transcriptSecondHop]: () => vtt(VTT_BODY(TRANSCRIPT_MARKER)),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    const out = await client.fetchLinkContent(FEED_URL);

    expect(called(stub, firstHop)).toBe(true);
    expect(called(stub, PUBLIC.transcriptSecondHop)).toBe(true);
    expect(out.content).toContain(TRANSCRIPT_MARKER);
  });
});
