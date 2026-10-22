/**
 * The SPARQL query tool takes an endpoint address from the caller; an endpoint
 * name that resolves to an internal address must not be contacted.
 */
import { afterEach, describe, expect, it } from "vitest";
import {
  callTool,
  Canary,
  connectMcp,
  McpHandle,
  refusalReported,
  startTcpCanary
} from "../helpers";

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

async function tcpCanary(): Promise<Canary> {
  const canary = await startTcpCanary();
  canaries.push(canary);
  return canary;
}

describe("SPARQL endpoint addresses supplied by the caller", () => {
  it("does not connect to a loopback address behind an endpoint name", async () => {
    const canary = await tcpCanary();
    const { client } = await mcp();

    const result = await callTool(client, "sparql_query", {
      endpoint_url: `https://sparql-a.test:${canary.port}/sparql`,
      query: "SELECT * WHERE { ?s ?p ?o }"
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });

  it("does not connect when an endpoint name resolves to a public and an internal address", async () => {
    const canary = await tcpCanary();
    const { client } = await mcp();

    const result = await callTool(client, "sparql_query", {
      endpoint_url: `https://portal-mixed.test:${canary.port}/sparql`,
      query: "SELECT * WHERE { ?s ?p ?o }"
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });
});
