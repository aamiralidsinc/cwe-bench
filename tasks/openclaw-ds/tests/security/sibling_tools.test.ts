// Tools outside the document module are governed by the same per-account configuration.
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

describe("other tools that act through an account", () => {
  test("chat lookups are refused when the request names a chat-off account", async () => {
    const chat = await import("../../chat.js");
    const h = createToolHarness(twoAccounts({ chat: false }, { chat: true }));
    chat.registerFeishuChatTools(h.api);

    const result = await h
      .tool("feishu_chat")
      .execute("call", { action: "info", chat_id: "chat-id", accountId: "a" });
    expectRefused(result);
  });

  test("bulk record creation is refused for the session account that has Bitable off", async () => {
    const bitable = await import("../../bitable.js");
    const h = createToolHarness(twoAccounts({ bitable: false }, { bitable: true }));
    bitable.registerFeishuBitableTools(h.api);

    const result = await h
      .tool("feishu_bitable_batch_create_records", { agentAccountId: "a" })
      .execute("call", {
        app_token: "app-token",
        table_id: "table-id",
        records: [{ Name: "first" }],
      });
    expectRefused(result);
  });
});
