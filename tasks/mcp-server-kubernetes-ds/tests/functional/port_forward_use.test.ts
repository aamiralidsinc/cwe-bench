/**
 * Ordinary port forwarding keeps working, with and without a namespace.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

import { ServerHandle, startServer } from "../helpers";

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

describe("ordinary port forwarding", () => {
  it("forwards a local port to a service", async () => {
    const outcome = await server.callTool("port_forward", {
      resourceType: "service",
      resourceName: "web",
      localPort: 8080,
      targetPort: 80,
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain("port-forwarding was successful");
    expect(server.kubectl()[0]).toEqual(["port-forward", "service/web", "8080:80"]);
  });

  it("forwards in a named namespace", async () => {
    const outcome = await server.callTool("port_forward", {
      resourceType: "pod",
      resourceName: "api-0",
      localPort: 9090,
      targetPort: 9000,
      namespace: "backend",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["port-forward", "-n", "backend", "pod/api-0", "9090:9000"]);
  });
});
