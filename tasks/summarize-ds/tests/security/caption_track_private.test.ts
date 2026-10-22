import { describe, it } from "vitest";
import { createLinkPreviewClient } from "@app/core";
import {
  INTERNAL,
  PAGE_URL,
  VTT_BODY,
  expectNoNonPublicFetch,
  html,
  makeFetch,
  vtt,
} from "../helpers.js";

describe("page-declared caption track destinations", () => {
  it("does not fetch a caption track on a loopback address", async () => {
    const mediaUrl = "https://media.summarize-test.example/video.mp4";
    const page =
      `<html><body><video src="${mediaUrl}">` +
      `<track kind="captions" src="${INTERNAL.loopback}" type="text/vtt" srclang="en">` +
      `</video></body></html>`;
    const stub = makeFetch({
      [PAGE_URL]: () => html(page),
      [INTERNAL.loopback]: () => vtt(VTT_BODY("internal-caption")),
    });
    const client = createLinkPreviewClient({ fetch: stub.impl, env: {} });

    await client.fetchLinkContent(PAGE_URL).catch(() => undefined);

    expectNoNonPublicFetch(stub);
  });
});
