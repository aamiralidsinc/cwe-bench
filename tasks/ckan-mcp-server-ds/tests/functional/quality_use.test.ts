/**
 * Legitimate use of the MQA quality tools: a public service base supplied by
 * the caller is used as given, and the dataset identifier is still resolved
 * from the portal when the caller does not provide one.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import { callTool, connectMcp, McpHandle, refusalReported, resultText } from "../helpers";

vi.mock("axios");

const MQA = {
  success: true,
  result: { count: 1, results: [{ info: { "dataset-id": "demo-1", score: 395 } }] }
};

const METRICS = {
  "@graph": [
    {
      "@id": "_:dataset-quality",
      "dqv:isMeasurementOf": { "@id": "https://piveau.eu/ns/voc#accessibilityScoring" },
      "dqv:value": { "@value": "90", "@type": "http://www.w3.org/2001/XMLSchema#int" }
    }
  ]
};

const PACKAGE_SHOW = {
  success: true,
  result: { identifier: "demo-2", name: "demo-dataset" }
};

let handles: McpHandle[] = [];

beforeEach(() => {
  vi.mocked(axios.get).mockReset();
  vi.mocked(axios.get).mockImplementation((async (url: string) => {
    const target = String(url);
    if (target.includes("/api/3/action/package_show")) return { data: PACKAGE_SHOW, headers: {} };
    if (target.includes("/api/mqa/cache/datasets")) return { data: MQA, headers: {} };
    return { data: {}, headers: {} };
  }) as never);

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const target = String(input);
      const body = target.includes("/api/mqa/cache/datasets") ? MQA : METRICS;
      return {
        ok: true,
        status: 200,
        statusText: "OK",
        headers: { get: () => "application/json" },
        json: async () => body,
        text: async () => JSON.stringify(body)
      };
    })
  );
});

/** Every URL requested through either client the project uses. */
function requestedUrls(): string[] {
  return [
    ...vi.mocked(axios.get).mock.calls.map((call) => String(call[0])),
    ...vi.mocked(fetch).mock.calls.map((call) => String(call[0]))
  ];
}

afterEach(async () => {
  vi.unstubAllGlobals();
  for (const handle of handles) await handle.close();
  handles = [];
});

async function mcp(): Promise<McpHandle> {
  const handle = await connectMcp();
  handles.push(handle);
  return handle;
}

describe("legitimate MQA quality use", () => {
  it("uses a public MQA service base supplied by the caller", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_get_mqa_quality", {
      server_url: "https://www.dati.gov.it/opendata",
      dataset_id: "demo",
      identifier: "demo-1",
      mqa_base_url: "https://mqa.open.example"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("395");
    const urls = requestedUrls();
    expect(urls).toContain("https://mqa.open.example/api/mqa/cache/datasets/demo-1");
    expect(urls).toContain("https://mqa.open.example/api/hub/repo/datasets/demo-1/metrics");
  });

  it("resolves the identifier from the portal when none is supplied", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_get_mqa_quality", {
      server_url: "https://www.dati.gov.it/opendata",
      dataset_id: "demo-dataset"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("395");
    const urls = requestedUrls();
    expect(urls.some((url) => url.includes("package_show"))).toBe(true);
    expect(urls.some((url) => url.endsWith("/api/mqa/cache/datasets/demo-2"))).toBe(true);
  });
});
