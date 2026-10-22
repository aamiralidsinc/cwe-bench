import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  INTERNAL,
  VTT_BODY,
  expectNoNonPublicFetch,
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

describe("embedded episode transcript destinations", () => {
  it("does not fetch an embedded transcript on a loopback address", async () => {
    const stub = makeFetch({
      [EMBED_URL]: () => html(embedHtml(INTERNAL.spotify)),
      [INTERNAL.spotify]: () => vtt(VTT_BODY("internal-spotify")),
    });
    const client = createLinkPreviewClient({
      fetch: stub.impl,
      env: {},
      openaiApiKey: "verifier-test-key",
    });

    await client.fetchLinkContent(EPISODE_URL).catch(() => undefined);

    expectNoNonPublicFetch(stub);
  });
});
