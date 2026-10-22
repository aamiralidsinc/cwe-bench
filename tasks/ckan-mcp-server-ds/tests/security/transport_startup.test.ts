/**
 * The network-facing transport must refuse to start unless the permitted hosts
 * have been configured. Driven through the real entry point (the bundled
 * server), so any implementation of the rule is accepted.
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { pickFreePort } from "../helpers";

const PROJECT_ROOT = process.env.PROJECT_ROOT ?? "/workspace";

function waitForExit(child: ReturnType<typeof spawn>, ms: number): Promise<number | null> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), ms);
    child.once("exit", (code) => {
      clearTimeout(timer);
      resolve(code);
    });
    child.once("error", () => {
      clearTimeout(timer);
      resolve(-1);
    });
  });
}

describe("network transport startup", () => {
  it("refuses to serve without a permitted-hosts list", async () => {
    const port = await pickFreePort();
    const env = { ...process.env, TRANSPORT: "http", PORT: String(port) };
    delete env.CKAN_ALLOWED_DOMAINS;
    delete env.CKAN_HTTP_ALLOW_ALL;

    const child = spawn("node", [path.join(PROJECT_ROOT, "dist/index.js")], {
      env,
      stdio: ["ignore", "pipe", "pipe"]
    });

    const code = await waitForExit(child, 8000);
    if (code === null) {
      child.kill("SIGKILL");
    }

    // It must not have kept serving; a refusal means the process ends.
    expect(code).not.toBeNull();
  });
});
