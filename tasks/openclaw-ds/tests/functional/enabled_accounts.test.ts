// Allowed use of every tool family keeps working next to an account that disables it.
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

describe("operations the operator allows keep working", () => {
  test("documents work on the session account that has them on", async () => {
    const docx = await import("../../docx.js");
    const h = createToolHarness(twoAccounts({ doc: false }, { doc: true }));
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc", { agentAccountId: "b" })
      .execute("call", { action: "list_blocks", doc_token: "doc-token" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });

  test("wiki works on the session account that has it on", async () => {
    const wiki = await import("../../wiki.js");
    const h = createToolHarness(twoAccounts({ wiki: false }, { wiki: true }));
    wiki.registerFeishuWikiTools(h.api);

    const result = await h
      .tool("feishu_wiki", { agentAccountId: "b" })
      .execute("call", { action: "spaces" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });

  test("drive works on the session account that has it on", async () => {
    const drive = await import("../../drive.js");
    const h = createToolHarness(twoAccounts({ drive: false }, { drive: true }));
    drive.registerFeishuDriveTools(h.api);

    const result = await h
      .tool("feishu_drive", { agentAccountId: "b" })
      .execute("call", { action: "list", folder_token: "folder-token" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });

  test("permissions work on the session account that has them on", async () => {
    const perm = await import("../../perm.js");
    const h = createToolHarness(twoAccounts({ perm: false }, { perm: true }));
    perm.registerFeishuPermTools(h.api);

    const result = await h
      .tool("feishu_perm", { agentAccountId: "b" })
      .execute("call", { action: "list", token: "doc-token", type: "doc" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });

  test("the scope diagnostic works when documents are off for that account", async () => {
    const docx = await import("../../docx.js");
    const h = createToolHarness(
      twoAccounts({ doc: false, scopes: true }, { doc: true, scopes: false }),
    );
    docx.registerFeishuDocTools(h.api);

    const result = await h.tool("feishu_app_scopes", { agentAccountId: "a" }).execute("call", {});
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-a");
  });

  test("documents work when the scope diagnostic is off for that account", async () => {
    const docx = await import("../../docx.js");
    const h = createToolHarness(
      twoAccounts({ doc: true, scopes: false }, { doc: false, scopes: true }),
    );
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc", { agentAccountId: "a" })
      .execute("call", { action: "list_blocks", doc_token: "doc-token" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-a");
  });

  test("chat lookups work on the account the request names when it has chat on", async () => {
    const chat = await import("../../chat.js");
    const h = createToolHarness(twoAccounts({ chat: false }, { chat: true }));
    chat.registerFeishuChatTools(h.api);

    const result = await h
      .tool("feishu_chat")
      .execute("call", { action: "info", chat_id: "chat-id", accountId: "b" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });

  test("Bitable metadata works on the session account that has Bitable on", async () => {
    const bitable = await import("../../bitable.js");
    const h = createToolHarness(twoAccounts({ bitable: false }, { bitable: true }));
    bitable.registerFeishuBitableTools(h.api);

    const result = await h
      .tool("feishu_bitable_get_meta", { agentAccountId: "b" })
      .execute("call", { url: "https://example.feishu.cn/base/apptoken123?table=tbl123" });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });

  test("bulk record creation works on the session account that has Bitable on", async () => {
    const bitable = await import("../../bitable.js");
    const h = createToolHarness(twoAccounts({ bitable: false }, { bitable: true }));
    bitable.registerFeishuBitableTools(h.api);

    const result = await h
      .tool("feishu_bitable_batch_create_records", { agentAccountId: "b" })
      .execute("call", {
        app_token: "app-token",
        table_id: "table-id",
        records: [{ Name: "first" }],
      });
    expectWorked(result);
    expect(rec.clients.at(-1)?.appId).toBe("app-b");
  });
});
