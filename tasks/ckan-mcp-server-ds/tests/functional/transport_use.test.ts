/**
 * The network transport starts when the permitted hosts are configured, and the
 * local stdio transport is unaffected by that requirement.
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { pickFreePort, portAccepts, sleep } from "../helpers";

const PROJECT_ROOT = process.env.PROJECT_ROOT ?? "/workspace";

const children: Array<ReturnType<typeof spawn>> = [];

afterEach(() => {
  for (const child of children) {
    try {
      child.kill("SIGKILL");
    } catch {
      // already gone
    }
  }
  children.length = 0;
});

async function waitForPort(port: number, ms: number): Promise<boolean> {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    if (await portAccepts(port, 300)) return true;
    await sleep(150);
  }
  return false;
}

describe("transport startup", () => {
  it("serves over HTTP when the permitted hosts are configured", async () => {
    const port = await pickFreePort();
    const env = {
      ...process.env,
      TRANSPORT: "http",
      PORT: String(port),
      CKAN_ALLOWED_DOMAINS: "open.portal.example"
    };
    delete env.CKAN_HTTP_ALLOW_ALL;
    const child = spawn("node", [path.join(PROJECT_ROOT, "dist/index.js")], {
      env,
      stdio: ["ignore", "pipe", "pipe"]
    });
    children.push(child);

    const started = await waitForPort(port, 12000);
    expect(started).toBe(true);
  });

  it("keeps the stdio transport available without a permitted-hosts list", async () => {
    const env = { ...process.env, TRANSPORT: "stdio" };
    delete env.CKAN_ALLOWED_DOMAINS;
    delete env.CKAN_HTTP_ALLOW_ALL;
    const child = spawn("node", [path.join(PROJECT_ROOT, "dist/index.js")], {
      env,
      stdio: ["pipe", "pipe", "pipe"]
    });
    children.push(child);

    await sleep(2500);
    expect(child.exitCode).toBeNull();
  });
});
