/**
 * Legitimate SPARQL use must keep working: a public HTTPS endpoint is queried,
 * non-HTTPS endpoints are still refused.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { callTool, connectMcp, McpHandle, refusalReported, resultText } from "../helpers";

const SAMPLE = {
  head: { vars: ["publisherName", "count"] },
  results: {
    bindings: [
      { publisherName: { type: "literal", value: "ISTAT" }, count: { type: "literal", value: "42" } }
    ]
  }
};

let handles: McpHandle[] = [];

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      headers: { get: () => "application/sparql-results+json" },
      json: async () => SAMPLE,
      text: async () => JSON.stringify(SAMPLE)
    }))
  );
});

afterEach(async () => {
  vi.unstubAllGlobals();
  for (const handle of handles) await handle.close();
  handles = [];
  delete process.env.CKAN_ALLOWED_DOMAINS;
});

async function mcp(): Promise<McpHandle> {
  const handle = await connectMcp();
  handles.push(handle);
  return handle;
}

describe("legitimate SPARQL use", () => {
  it("queries a public HTTPS endpoint", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "sparql_query", {
      endpoint_url: "https://sparql.open.example/sparql",
      query: "SELECT ?publisherName (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("ISTAT");
  });

  it("still refuses a non-HTTPS endpoint", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "sparql_query", {
      endpoint_url: "http://open.portal.example/sparql",
      query: "SELECT * WHERE { ?s ?p ?o }"
    });

    expect(refusalReported(result)).toBe(true);
    expect(vi.mocked(fetch).mock.calls.length).toBe(0);
  });
});
