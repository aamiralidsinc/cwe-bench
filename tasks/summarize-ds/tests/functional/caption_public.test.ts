import { describe, expect, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  CAPTION_MARKER,
  PAGE_URL,
  PUBLIC,
  VTT_BODY,
  called,
  html,
  makeFetch,
  vtt,
} from "../helpers.js";

describe("legitimate page caption tracks", () => {
  it("fetches a public caption track and returns its text", async () => {
    const mediaUrl = "https://media.summarize-test.example/video.mp4";
    const page =
      `<html><body><video src="${mediaUrl}">` +
      `<track kind="captions" src="${PUBLIC.caption}" type="text/vtt" srclang="en">` +
      `</video></body></html>`;
    const stub = makeFetch({
      [PAGE_URL]: () => html(page),
      [PUBLIC.caption]: () => vtt(VTT_BODY(CAPTION_MARKER)),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    const out = await client.fetchLinkContent(PAGE_URL);

    expect(called(stub, PUBLIC.caption)).toBe(true);
    expect(out.content).toContain(CAPTION_MARKER);
  });
});
