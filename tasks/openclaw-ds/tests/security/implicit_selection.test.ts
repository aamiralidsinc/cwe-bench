// A request that names no account must not run under an account that has the tool off.
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

function expectRefused(result: { details?: Record<string, unknown> }) {
  expect(hasError(result), `expected an error result, got ${JSON.stringify(result.details)}`).toBe(
    true,
  );
  expect(rec.calls, `operations ran: ${JSON.stringify(rec.calls)}`).toEqual([]);
}

beforeEach(() => {
  rec.reset();
});

describe("requests that name no account", () => {
  test("do not run under an account that has the tool off", async () => {
    const wiki = await import("../../wiki.js");
    // No session account and no configured default: the product's default selection is the
    // first account, which has wiki off, while the second account has it on.
    const h = createToolHarness(twoAccounts({ wiki: false }, { wiki: true }));
    wiki.registerFeishuWikiTools(h.api);

    const result = await h.tool("feishu_wiki").execute("call", { action: "spaces" });
    const usedOffAccount = rec.calls.some((call) => call.appId === "app-a");
    expect(
      usedOffAccount,
      `the wiki-off account was used: ${JSON.stringify(rec.calls)} (result ${JSON.stringify(result.details)})`,
    ).toBe(false);
  });

  test("do not run under a configured default account that has the tool off", async () => {
    const docx = await import("../../docx.js");
    const h = createToolHarness(
      twoAccounts({ doc: false }, { doc: true }, { defaultAccount: "a" }),
    );
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc")
      .execute("call", { action: "list_blocks", doc_token: "doc-token" });
    const usedOffAccount = rec.calls.some((call) => call.appId === "app-a");
    expect(
      usedOffAccount,
      `the documents-off account was used: ${JSON.stringify(rec.calls)} (result ${JSON.stringify(result.details)})`,
    ).toBe(false);
  });
});
