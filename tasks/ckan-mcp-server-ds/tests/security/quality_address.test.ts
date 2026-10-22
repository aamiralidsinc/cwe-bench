/**
 * The MQA quality tools fetch from the quality service. A caller-supplied
 * service base is a destination like any other; a name that resolves to an
 * internal address must not be contacted.
 */
import { afterEach, describe, expect, it } from "vitest";
import {
  callTool,
  Canary,
  connectMcp,
  McpHandle,
  refusalReported,
  resultText,
  startHttpCanary
} from "../helpers";

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

let canaries: Canary[] = [];
let handles: McpHandle[] = [];

afterEach(async () => {
  for (const handle of handles) await handle.close();
  for (const canary of canaries) await canary.close();
  handles = [];
  canaries = [];
});

async function qualityCanary(): Promise<Canary> {
  const canary = await startHttpCanary((req, res) => {
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify(req.url && req.url.includes("/metrics") ? METRICS : MQA));
  });
  canaries.push(canary);
  return canary;
}

function errorVisible(result: { isError?: boolean; content?: Array<{ text?: string }> }): boolean {
  return refusalReported(result) || /error/i.test(resultText(result));
}

describe("quality service addresses supplied by the caller", () => {
  it("does not connect to a loopback address behind an MQA service base", async () => {
    const canary = await qualityCanary();
    const handle = await connectMcp();
    handles.push(handle);

    const result = await callTool(handle.client, "ckan_get_mqa_quality", {
      server_url: "https://www.dati.gov.it/opendata",
      dataset_id: "demo",
      identifier: "demo-1",
      mqa_base_url: `http://mqa-a.test:${canary.port}`
    });

    expect(canary.hits).toBe(0);
    expect(errorVisible(result)).toBe(true);
  });

  it("does not connect to a loopback address behind an MQA service base (details)", async () => {
    const canary = await qualityCanary();
    const handle = await connectMcp();
    handles.push(handle);

    const result = await callTool(handle.client, "ckan_get_mqa_quality_details", {
      server_url: "https://www.dati.gov.it/opendata",
      dataset_id: "demo",
      identifier: "demo-1",
      mqa_base_url: `http://mqa-a.test:${canary.port}`
    });

    expect(canary.hits).toBe(0);
    expect(errorVisible(result)).toBe(true);
  });
});
