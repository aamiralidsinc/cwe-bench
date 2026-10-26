/**
 * Ordinary chart operations keep working, including template mode.
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

describe("ordinary chart use", () => {
  it("installs a chart from a repository", async () => {
    const outcome = await server.callTool("install_helm_chart", {
      name: "web",
      chart: "nginx",
      repo: "https://charts.example",
      namespace: "default",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain('"status":"installed"');
    expect(server.helm().flat()).toEqual(expect.arrayContaining(["install", "web", "nginx"]));
  });

  it("upgrades a chart", async () => {
    const outcome = await server.callTool("upgrade_helm_chart", {
      name: "web",
      chart: "nginx",
      namespace: "default",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain('"status":"upgraded"');
    expect(server.helm().flat()).toEqual(expect.arrayContaining(["upgrade", "web", "nginx"]));
  });

  it("uninstalls a chart", async () => {
    const outcome = await server.callTool("uninstall_helm_chart", {
      name: "web",
      namespace: "default",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain('"status":"uninstalled"');
    expect(server.helm().flat()).toEqual(expect.arrayContaining(["uninstall", "web"]));
  });

  it("installs a chart in template mode", async () => {
    const outcome = await server.callTool("install_helm_chart", {
      name: "web",
      chart: "nginx",
      namespace: "default",
      useTemplate: true,
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain("installed");
    expect(server.helm().flat()).toEqual(expect.arrayContaining(["template", "web", "nginx"]));
  });
});
