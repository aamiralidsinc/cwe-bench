import { describe, expect, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  PUBLIC,
  SPOTIFY_MARKER,
  VTT_BODY,
  called,
  html,
  makeFetch,
  vtt,
} from "../helpers.js";

const EMBED_URL = "https://open.spotify.com/embed/episode/abc";
const EPISODE_URL = "https://open.spotify.com/episode/abc";

function embedHtml(transcriptUrl: string): string {
  return `<html><script id="__NEXT_DATA__">${JSON.stringify({
    props: {
      pageProps: {
        state: {
          data: { entity: { subtitle: "Show", title: "Episode", transcriptUrl } },
        },
      },
    },
  })}</script></html>`;
}

describe("legitimate embedded episode transcripts", () => {
  it("still fetches an embedded transcript from a public address", async () => {
    const stub = makeFetch({
      [EMBED_URL]: () => html(embedHtml(PUBLIC.spotifyTranscript)),
      [PUBLIC.spotifyTranscript]: () => vtt(VTT_BODY(SPOTIFY_MARKER)),
    });
    const client = createLinkPreviewClient({
      fetch: stub.impl,
      env: {},
      openaiApiKey: "verifier-test-key",
    });

    const out = await client.fetchLinkContent(EPISODE_URL);

    expect(called(stub, PUBLIC.spotifyTranscript)).toBe(true);
    expect(out.content).toContain(SPOTIFY_MARKER);
  });
});
