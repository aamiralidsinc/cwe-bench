/**
 * Legitimate use of the registry and preview entry points must keep working.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import { callTool, connectMcp, McpHandle, refusalReported, resultText } from "../helpers";

vi.mock("axios");

const REGISTRY = {
  portals: [
    {
      Href: "https://open.portal.example",
      SiteInfo: { site_title: "Open Portal", locale_default: "en" },
      Coordinates: { country_name: "Italy" },
      Version: "2.9",
      Plugins: ["datastore"],
      DatasetsNumber: 120,
      OrgNumber: 3,
      status: "active"
    }
  ]
};

let handles: McpHandle[] = [];

beforeEach(() => {
  vi.mocked(axios.get).mockReset();
  vi.mocked(axios.get).mockResolvedValue({ data: REGISTRY, headers: {} } as never);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      headers: { get: () => "text/csv" },
      text: async () => "id,name\n1,alpha\n2,beta\n",
      json: async () => ({})
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

describe("legitimate registry and preview use", () => {
  it("lists portals from the default public registry", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_find_portals", { country: "Italy" });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("Open Portal");
    expect(vi.mocked(axios.get).mock.calls[0][0]).toContain("datashades.info");
  });

  it("lists portals from a public alternative registry", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_find_portals", {
      registry_url: "https://registry.open.example/list",
      country: "Italy"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("Open Portal");
    // The supplied registry is the one that is read.
    expect(vi.mocked(axios.get).mock.calls[0][0]).toBe("https://registry.open.example/list");
  });

  it("reports reachability for portals listed by a public registry", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_find_portals", {
      registry_url: "https://registry.open.example/list",
      country: "Italy",
      verify: true
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toMatch(/reachable/i);
    // The portal address from the registry is the one that is probed, whichever
    // client the implementation uses.
    const probed = [
      ...vi.mocked(fetch).mock.calls.map((call) => String(call[0])),
      ...vi.mocked(axios.get).mock.calls.map((call) => String(call[0]))
    ];
    expect(probed).toContain("https://open.portal.example");
  });

  it("does not probe portals when reachability was not requested", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_find_portals", {
      registry_url: "https://registry.open.example/list",
      country: "Italy"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("Open Portal");
    const touched = [
      ...vi.mocked(fetch).mock.calls.map((call) => String(call[0])),
      ...vi.mocked(axios.get).mock.calls.map((call) => String(call[0]))
    ];
    expect(touched).not.toContain("https://open.portal.example");
  });

  it("previews a resource from a public download URL", async () => {
    const { client } = await mcp();
    const result = await callTool(client, "ckan_resource_preview", {
      url: "https://preview.open.example/data.csv"
    });

    expect(refusalReported(result)).toBe(false);
    expect(resultText(result)).toContain("alpha");
    // The supplied download URL is the one that is fetched.
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe("https://preview.open.example/data.csv");
  });
});
