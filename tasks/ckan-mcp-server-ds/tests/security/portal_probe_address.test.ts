/**
 * The portal-discovery reachability option probes the portal addresses the
 * registry lists. Those addresses are taken from another service's response;
 * a name that resolves to an internal address must not be contacted.
 */
import http from "node:http";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import {
  callTool,
  Canary,
  ckanJson,
  connectMcp,
  McpHandle,
  refusalReported,
  resultText,
  startHttpCanary
} from "../helpers";

vi.mock("axios");

const realFetch = globalThis.fetch;

function registryWith(href: string) {
  return {
    portals: [
      {
        Href: href,
        SiteInfo: { site_title: "Open Portal", locale_default: "en" },
        Coordinates: { country_name: "Italy" },
        Version: "2.9",
        Plugins: ["datastore"],
        DatasetsNumber: 10,
        OrgNumber: 2,
        status: "active"
      }
    ]
  };
}

let canaries: Canary[] = [];
let handles: McpHandle[] = [];
let listedHref = "";

/** Was the internal address actually contacted? Any client may be used by a fix. */
async function recordHttpAttempt(url: string): Promise<void> {
  await new Promise<void>((resolve) => {
    const req = http.request(url, (res) => {
      res.resume();
      res.on("end", () => resolve());
    });
    req.on("error", () => resolve());
    req.end();
  });
}

beforeEach(() => {
  vi.mocked(axios.get).mockReset();
  vi.mocked(axios.get).mockImplementation((async (url: string) => {
    const target = String(url);
    if (target.includes("portal-a.test")) {
      await recordHttpAttempt(target);
      return { data: {}, headers: {} };
    }
    return { data: registryWith(listedHref), headers: {} };
  }) as never);

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: unknown) => {
      const target = String(input);
      if (target.includes("portal-a.test")) {
        return realFetch(input as RequestInfo, init as RequestInit);
      }
      return new Response(JSON.stringify(registryWith(listedHref)), {
        status: 200,
        headers: { "content-type": "application/json" }
      });
    })
  );
});

afterEach(async () => {
  vi.unstubAllGlobals();
  for (const handle of handles) await handle.close();
  for (const canary of canaries) await canary.close();
  handles = [];
  canaries = [];
  listedHref = "";
});

describe("portal addresses taken from the registry response", () => {
  it("does not connect to a loopback address when probing the listed portals", async () => {
    const canary = await startHttpCanary(ckanJson({ ok: true }));
    canaries.push(canary);
    listedHref = `http://portal-a.test:${canary.port}/portal`;

    const handle = await connectMcp();
    handles.push(handle);

    const result = await callTool(handle.client, "ckan_find_portals", {
      registry_url: "https://registry.open.example/list",
      country: "Italy",
      verify: true
    });

    expect(canary.hits).toBe(0);
    expect(
      refusalReported(result) || /not reachable|unreachable|error/i.test(resultText(result))
    ).toBe(true);
  });
});
