// The account a tool runs as is the account whose own configuration governs it, however the
// account was chosen. Each case here drives the real registered tool and records every call
// that reaches the Feishu client.
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

let docx: typeof import("../../docx.js");
let wiki: typeof import("../../wiki.js");
let drive: typeof import("../../drive.js");
let perm: typeof import("../../perm.js");

async function modules() {
  docx ??= await import("../../docx.js");
  wiki ??= await import("../../wiki.js");
  drive ??= await import("../../drive.js");
  perm ??= await import("../../perm.js");
}

beforeEach(() => {
  rec.reset();
});

function expectRefused(result: { details?: Record<string, unknown> }) {
  expect(hasError(result), `expected an error result, got ${JSON.stringify(result.details)}`).toBe(
    true,
  );
  expect(rec.calls, `operations ran: ${JSON.stringify(rec.calls)}`).toEqual([]);
}

describe("per-account tool configuration at execution", () => {
  test("document read is refused for the session account that has documents off", async () => {
    await modules();
    const h = createToolHarness(twoAccounts({ doc: false }, { doc: true }));
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc", { agentAccountId: "a" })
      .execute("call", { action: "list_blocks", doc_token: "doc-token" });
    expectRefused(result);
  });

  test("document read is refused when the request names a documents-off account", async () => {
    await modules();
    const h = createToolHarness(twoAccounts({ doc: false }, { doc: true }));
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc", { agentAccountId: "b" })
      .execute("call", { action: "list_blocks", doc_token: "doc-token", accountId: "a" });
    expectRefused(result);
  });

  test("document write is refused for the session account that has documents off", async () => {
    await modules();
    const h = createToolHarness(twoAccounts({ doc: false }, { doc: true }));
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc", { agentAccountId: "a" })
      .execute("call", { action: "append", doc_token: "doc-token", content: "hello" });
    expectRefused(result);
  });

  test("wiki is refused when the request names a wiki-off account", async () => {
    await modules();
    const h = createToolHarness(twoAccounts({ wiki: false }, { wiki: true }));
    wiki.registerFeishuWikiTools(h.api);

    const result = await h
      .tool("feishu_wiki", { agentAccountId: "b" })
      .execute("call", { action: "spaces", accountId: "a" });
    expectRefused(result);
  });

  test("drive is refused for the session account that has drive off", async () => {
    await modules();
    const h = createToolHarness(twoAccounts({ drive: false }, { drive: true }));
    drive.registerFeishuDriveTools(h.api);

    const result = await h
      .tool("feishu_drive", { agentAccountId: "a" })
      .execute("call", { action: "list", folder_token: "folder-token" });
    expectRefused(result);
  });

  test("permissions are refused for the session account that has permissions off", async () => {
    await modules();
    const h = createToolHarness(twoAccounts({ perm: false }, { perm: true }));
    perm.registerFeishuPermTools(h.api);

    const result = await h
      .tool("feishu_perm", { agentAccountId: "a" })
      .execute("call", { action: "list", token: "doc-token", type: "doc" });
    expectRefused(result);
  });

  test("an account that never enables a tool is refused when that tool is off by default", async () => {
    await modules();
    // Only account a enables permissions. Account b says nothing about tools at all, so its
    // effective permissions setting is the product default, which is off.
    const h = createToolHarness(twoAccounts({ perm: true }, {}));
    perm.registerFeishuPermTools(h.api);

    const result = await h
      .tool("feishu_perm", { agentAccountId: "b" })
      .execute("call", { action: "list", token: "doc-token", type: "doc" });
    expectRefused(result);
  });
});
