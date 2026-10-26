/**
 * Ordinary kubectl use keeps working: names, types, namespaces, selectors,
 * output formats, context selection and ordinary flags are passed through
 * unchanged.
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

describe("ordinary kubectl use", () => {
  it("lists pods in the default namespace", async () => {
    const outcome = await server.callTool("kubectl_get", { resourceType: "pods" });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["get", "pods", "-n", "default", "-o", "json"]);
  });

  it("keeps names, namespaces, selectors, output formats and a selected context", async () => {
    const outcome = await server.callTool("kubectl_get", {
      resourceType: "pods",
      name: "nginx",
      namespace: "prod",
      output: "wide",
      labelSelector: "app=web",
      fieldSelector: "status.phase=Running",
      context: "ctx",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual([
      "get",
      "pods",
      "nginx",
      "-n",
      "prod",
      "--context",
      "ctx",
      "-l",
      "app=web",
      "--field-selector=status.phase=Running",
      "-o",
      "wide",
    ]);
  });

  it("describes a pod with a selected context", async () => {
    const outcome = await server.callTool("kubectl_describe", {
      resourceType: "pod",
      name: "nginx",
      context: "ctx",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["describe", "pod", "nginx", "-n", "default", "--context", "ctx"]);
  });

  it("creates a namespace by name", async () => {
    const outcome = await server.callTool("kubectl_create", { resourceType: "namespace", name: "demo" });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0].slice(0, 3)).toEqual(["create", "namespace", "demo"]);
  });

  it("scales a deployment", async () => {
    const outcome = await server.callTool("kubectl_scale", {
      name: "web",
      resourceType: "deployment",
      replicas: 3,
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual([
      "scale",
      "deployment",
      "web",
      "--replicas=3",
      "--namespace=default",
    ]);
  });

  it("accepts ordinary caller-supplied options in the generic tool", async () => {
    const outcome = await server.callTool("kubectl_generic", {
      command: "get",
      resourceType: "pods",
      flags: { output: "wide" },
      args: ["--sort-by", ".metadata.name"],
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["get", "pods", "--output=wide", "--sort-by", ".metadata.name"]);
  });

  it("covers a node by name", async () => {
    const outcome = await server.callTool("node_management", {
      operation: "cordon",
      nodeName: "node-1",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl().flat()).toEqual(expect.arrayContaining(["node-1", "cordon"]));
  });

  it("explains a resource", async () => {
    const outcome = await server.callTool("explain_resource", { resource: "pods" });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain("RESOURCE: pods");
  });

  it("selects an existing context by name", async () => {
    const outcome = await server.callTool("kubectl_context", { operation: "set", name: "ctx" });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain("Current context set to 'ctx'");
  });

  it("lists contexts", async () => {
    const outcome = await server.callTool("kubectl_context", { operation: "list", output: "json" });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    const parsed = JSON.parse(outcome.text) as { contexts: unknown[] };
    expect(parsed.contexts.length).toBe(2);
  });

  it("fetches logs from a named pod", async () => {
    const outcome = await server.callTool("kubectl_logs", {
      resourceType: "pod",
      name: "nginx",
      namespace: "default",
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(outcome.text).toContain("hello from pod");
  });
});
