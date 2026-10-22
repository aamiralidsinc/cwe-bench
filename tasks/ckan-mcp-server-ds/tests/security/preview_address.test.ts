/**
 * The resource-preview tool fetches a caller-supplied download URL. That
 * address must not reach an internal service.
 */
import { afterEach, describe, expect, it } from "vitest";
import {
  callTool,
  Canary,
  connectMcp,
  McpHandle,
  refusalReported,
  startHttpCanary,
  textResponse
} from "../helpers";

let canaries: Canary[] = [];
let handles: McpHandle[] = [];

afterEach(async () => {
  for (const handle of handles) await handle.close();
  for (const canary of canaries) await canary.close();
  handles = [];
  canaries = [];
});

describe("resource download address supplied by the caller", () => {
  it("does not connect to a loopback address behind a resource URL", async () => {
    const canary = await startHttpCanary(textResponse("text/csv", "id,name\n1,internal\n"));
    canaries.push(canary);
    const handle = await connectMcp();
    handles.push(handle);

    const result = await callTool(handle.client, "ckan_resource_preview", {
      url: `http://preview-a.test:${canary.port}/data.csv`
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });
});
