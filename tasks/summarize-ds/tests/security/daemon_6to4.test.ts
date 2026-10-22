import { describe, expect, it } from "vitest";
import { INTERNAL, expectNoNonPublicFetch, makeFetch, postSummarize, startDaemon } from "../helpers.js";

describe("background summarizer URL mode", () => {
  it("refuses an IPv6 address that embeds a loopback IPv4 address through 6to4", async () => {
    const stub = makeFetch({});
    const daemon = await startDaemon(stub);
    try {
      const { status } = await postSummarize(daemon, INTERNAL.sixToFourLoopback);

      expect(status).toBeGreaterThanOrEqual(400);
      expect(status).toBeLessThan(500);
      expectNoNonPublicFetch(stub);
    } finally {
      await daemon.close();
    }
  });
});
