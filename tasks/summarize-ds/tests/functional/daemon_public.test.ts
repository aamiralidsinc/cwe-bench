import { describe, expect, it } from "vitest";
import {
  PAGE_URL,
  called,
  expectNoNonPublicFetch,
  html,
  makeFetch,
  postSummarize,
  startDaemon,
} from "../helpers.js";

describe("legitimate background summarizer use", () => {
  it("still summarizes a public page submitted in URL mode", async () => {
    const stub = makeFetch({
      [PAGE_URL]: () =>
        html("<!doctype html><html><head><title>Ok</title></head><body>Public article body</body></html>"),
    });
    const daemon = await startDaemon(stub);
    try {
      const { status } = await postSummarize(daemon, PAGE_URL);

      expect(status).toBeGreaterThanOrEqual(200);
      expect(status).toBeLessThan(300);
      expect(called(stub, PAGE_URL)).toBe(true);
      expectNoNonPublicFetch(stub);
    } finally {
      await daemon.close();
    }
  });

  it("still accepts a public IPv6 address that embeds a public IPv4 address", async () => {
    const nat64Public = "http://[64:ff9b::808:808]:8080/article";
    const stub = makeFetch({
      [nat64Public]: () =>
        html("<!doctype html><html><head><title>Ok</title></head><body>Public article body</body></html>"),
    });
    const daemon = await startDaemon(stub);
    try {
      const { status } = await postSummarize(daemon, nat64Public);

      expect(status).toBeGreaterThanOrEqual(200);
      expect(status).toBeLessThan(300);
      expect(called(stub, nat64Public)).toBe(true);
      expectNoNonPublicFetch(stub);
    } finally {
      await daemon.close();
    }
  });
});
