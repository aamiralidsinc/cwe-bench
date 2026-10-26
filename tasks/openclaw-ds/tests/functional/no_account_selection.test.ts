// Requests that name no account keep being served by an allowed account.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { createToolHarness, hasError, twoAccounts } from "../support.js";

const rec = vi.hoisted(() => {
  const clients: { appId?: string }[] = [];
  const calls: { appId?: string; path: string }[] = [];
  function node(appId: string | undefined, path: string): unknown {
    const fn = (..._args: unknown[]) => {
      calls.push({ appId, path });
      return Promise.resolve({ code: 0, msg: "ok", data: {} });
    };
    return new Proxy(fn, {
      get(_target, prop) {
        if (typeof prop === "symbol" || prop === "then") {
          return undefined;
        }
        return node(appId, `${path}.${String(prop)}`);
      },
    });
  }
  function makeClient(account: { appId?: string } | undefined) {
    clients.push(account ?? {});
    return node(account?.appId, "client");
  }
  return {
    clients,
    calls,
    makeClient,
    reset() {
      clients.length = 0;
      calls.length = 0;
    },
  };
});

vi.mock("../../client.js", () => ({
  createFeishuClient: (account: { appId?: string } | undefined) => rec.makeClient(account),
}));

beforeEach(() => {
  rec.reset();
});

function expectWorked(result: { details?: Record<string, unknown> }) {
  expect(hasError(result), `unexpected error: ${JSON.stringify(result.details)}`).toBe(false);
  expect(rec.calls.length, "no Feishu operation ran").toBeGreaterThan(0);
}

describe("requests that name no account keep being served", () => {
  test("a request without an account is served when one account has the tool on", async () => {
    const wiki = await import("../../wiki.js");
    // The default selection is the first account, which has wiki off; the second has it on.
    const h = createToolHarness(twoAccounts({ wiki: false }, { wiki: true }));
    wiki.registerFeishuWikiTools(h.api);

    const result = await h.tool("feishu_wiki").execute("call", { action: "spaces" });
    expectWorked(result);
  });

  test("a request without an account uses the default selection when it is allowed", async () => {
    const drive = await import("../../drive.js");
    const h = createToolHarness(twoAccounts({ drive: true }, { drive: true }));
    drive.registerFeishuDriveTools(h.api);

    const result = await h
      .tool("feishu_drive")
      .execute("call", { action: "list", folder_token: "folder-token" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-a");
  });
});
