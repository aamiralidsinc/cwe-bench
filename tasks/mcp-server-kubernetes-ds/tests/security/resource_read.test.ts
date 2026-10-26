/**
 * A resource read is a client request too. Its path segments become bare words
 * on the same kind of command line, so they are bound by the same rule.
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

describe("resource reads refuse caller values that would be options", () => {
  it("does not read through a different API server", async () => {
    const outcome = await server.readResource("k8s://raw/default/--server=attacker.example");

    await expectBlocked(server, outcome);
  });

  it("does not read with substituted credentials", async () => {
    const outcome = await server.readResource("k8s://raw/default/pods/--token=stolen");

    await expectBlocked(server, outcome);
  });
});
