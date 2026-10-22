/**
 * The portal address a caller passes to a CKAN tool, and the address a portal
 * redirects to, must never reach an internal service.
 */
import { afterEach, describe, expect, it } from "vitest";
import {
  callTool,
  ckanJson,
  connectMcp,
  McpHandle,
  Canary,
  refusalReported,
  startHttpCanary
} from "../helpers";

const SEARCH_RESULT = { success: true, result: { count: 0, results: [] } };
const STATUS_RESULT = {
  success: true,
  result: { ckan_version: "2.9.9", site_title: "internal", site_url: "http://internal.invalid" }
};

let canaries: Canary[] = [];
let handles: McpHandle[] = [];

afterEach(async () => {
  for (const handle of handles) await handle.close();
  for (const canary of canaries) await canary.close();
  handles = [];
  canaries = [];
});

async function mcp(): Promise<McpHandle> {
  const handle = await connectMcp();
  handles.push(handle);
  return handle;
}

async function httpCanary(body: unknown): Promise<Canary> {
  const canary = await startHttpCanary(ckanJson(body));
  canaries.push(canary);
  return canary;
}

describe("portal addresses supplied by the caller", () => {
  it("does not connect to a loopback address behind a dataset-search portal name", async () => {
    const canary = await httpCanary(SEARCH_RESULT);
    const { client } = await mcp();

    const result = await callTool(client, "ckan_package_search", {
      server_url: `http://portal-a.test:${canary.port}`,
      q: "istat"
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });

  it("does not connect to a loopback address behind a status-check portal name", async () => {
    const canary = await httpCanary(STATUS_RESULT);
    const { client } = await mcp();

    const result = await callTool(client, "ckan_status_show", {
      server_url: `http://portal-a.test:${canary.port}`
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });

  it("does not connect when a portal name resolves to a public and an internal address", async () => {
    const canary = await httpCanary(SEARCH_RESULT);
    const { client } = await mcp();

    const result = await callTool(client, "ckan_package_search", {
      server_url: `http://portal-mixed.test:${canary.port}`,
      q: "istat"
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });

  it("does not follow a redirect from a portal to a loopback address", async () => {
    const internal = await httpCanary(SEARCH_RESULT);
    const front = await startHttpCanary((_req, res) => {
      res.statusCode = 302;
      res.setHeader("location", `http://127.0.0.1:${internal.port}/api/3/action/package_search`);
      res.end();
    });
    canaries.push(front);
    const { client } = await mcp();

    await callTool(client, "ckan_package_search", {
      server_url: `http://portal-a.test:${front.port}`,
      q: "istat"
    });

    expect(internal.hits).toBe(0);
  });
});
