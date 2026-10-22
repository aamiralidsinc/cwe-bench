/**
 * The portal-discovery tool can be pointed at an alternative registry
 * endpoint. That address comes from the caller and must not reach an internal
 * service.
 */
import { afterEach, describe, expect, it } from "vitest";
import {
  callTool,
  ckanJson,
  Canary,
  connectMcp,
  McpHandle,
  refusalReported,
  startHttpCanary
} from "../helpers";

const REGISTRY = {
  portals: [
    {
      Href: "https://open.portal.example",
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

let canaries: Canary[] = [];
let handles: McpHandle[] = [];

afterEach(async () => {
  for (const handle of handles) await handle.close();
  for (const canary of canaries) await canary.close();
  handles = [];
  canaries = [];
});

describe("registry endpoint supplied by the caller", () => {
  it("does not connect to a loopback address behind a registry name", async () => {
    const canary = await startHttpCanary(ckanJson(REGISTRY));
    canaries.push(canary);
    const handle = await connectMcp();
    handles.push(handle);

    const result = await callTool(handle.client, "ckan_find_portals", {
      registry_url: `http://registry-a.test:${canary.port}/list`,
      country: "Italy"
    });

    expect(canary.hits).toBe(0);
    expect(refusalReported(result)).toBe(true);
  });
});
