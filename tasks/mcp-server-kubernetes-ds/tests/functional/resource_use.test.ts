/**
 * Ordinary reads through the resource surface keep working.
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

describe("ordinary resource reads", () => {
  it("reads a kind by name", async () => {
    const outcome = await server.readResource("k8s://raw/default/pods");

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["get", "pods", "-n", "default", "-o", "json"]);
    expect((outcome.contents ?? []).map((entry) => entry.text ?? "").join("\n")).toContain("PodList");
  });

  it("reads a single object by name", async () => {
    const outcome = await server.readResource("k8s://raw/default/pods/nginx");

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["get", "pods", "nginx", "-n", "default", "-o", "json"]);
  });
});
