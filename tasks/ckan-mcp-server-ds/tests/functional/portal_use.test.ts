/**
 * Legitimate CKAN portal use must keep working: public portals and public
 * literal addresses are still queried, private literals are still refused.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import { callTool, connectMcp, McpHandle, refusalReported, resultText } from "../helpers";

vi.mock("axios");

const SEARCH_RESULT = {
  success: true,
  result: {
    count: 2,
    results: [
      { title: "Popolazione residente", name: "popolazione-residente" },
      { title: "Ordinanze comunali", name: "ordinanze-comunali" }
    ]
  }
};

const STATUS_RESULT = { success: true, result: { ckan_version: "2.9.9", site_title: "Open Portal" } };

const SHOW_RESULT = {
  success: true,
  result: {
    name: "popolazione-residente",
    title: "Popolazione residente",
    id: "11111111-2222-3333-4444-555555555555"
  }
};

let handles: McpHandle[] = [];

beforeEach(() => {
  vi.mocked(axios.get).mockReset();
  vi.mocked(axios.get).mockImplementation((async (url: string) => {
    if (url.includes("package_search")) return { data: SEARCH_RESULT, headers: {} };
    if (url.includes("package_show")) return { data: SHOW_RESULT, headers: {} };
    return { data: STATUS_RESULT, headers: {} };
  }) as never);
});

afterEach(async () => {
  for (const handle of handles) await handle.close();
  handles = [];
  delete process.env.CKAN_ALLOWED_DOMAINS;
});

async function mcp(): Promise<McpHandle> {
  const handle = await connectMcp();
  handles.push(handle);
  return handle;
}

describe("legitimate portal use", () => {
  it("searches a public portal reached through an ordinary host name", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_package_search", {
      server_url: "https://open.portal.example",
      q: "popolazione"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("Popolazione residente");
    expect(vi.mocked(axios.get).mock.calls[0][0]).toBe(
      "https://open.portal.example/api/3/action/package_search"
    );
  });

  it("checks the status of a portal addressed by a public literal", async () => {
    const { client } = await mcp();
    for (const server of ["http://172.15.9.9", "http://100.63.9.9"]) {
      const result = await callTool(client, "ckan_status_show", { server_url: server });
      expect(refusalReported(result)).toBe(false);
    }
  });

  it("reads a ckan:// resource from a public portal", async () => {
    const { client } = await mcp();
    const result = (await client.readResource({
      uri: "ckan://open.portal.example/dataset/popolazione-residente"
    })) as { contents?: Array<{ text?: string }> };

    const text = (result.contents ?? []).map((entry) => entry.text ?? "").join("\n");
    expect(text).toContain("Popolazione residente");
  });

  it("still refuses loopback, private and metadata literals", async () => {
    const { client } = await mcp();
    for (const server of [
      "http://127.0.0.1",
      "http://10.1.2.3",
      "http://192.168.1.10",
      "http://169.254.169.254/latest/meta-data/",
      "http://[::1]"
    ]) {
      const result = await callTool(client, "ckan_status_show", { server_url: server });
      expect(refusalReported(result)).toBe(true);
    }
  });
});
