// The scope diagnostic and document work are separate tool families with separate settings.
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

describe("app scope diagnostics and the document tool", () => {
  test("the scope diagnostic is refused when the session account has it off", async () => {
    const docx = await import("../../docx.js");
    // The session account has documents on and the scope diagnostic off; another account
    // enables the diagnostic, so the tool is offered.
    const h = createToolHarness(
      twoAccounts({ doc: true, scopes: false }, { doc: false, scopes: true }),
    );
    docx.registerFeishuDocTools(h.api);

    const result = await h.tool("feishu_app_scopes", { agentAccountId: "a" }).execute("call", {});
    expectRefused(result);
  });

  test("documents are refused for the session account that has documents off", async () => {
    const docx = await import("../../docx.js");
    // The session account has documents off but the scope diagnostic on, so a check that uses
    // the diagnostic's setting for document work would let this through.
    const h = createToolHarness(
      twoAccounts({ doc: false, scopes: true }, { doc: true, scopes: false }),
    );
    docx.registerFeishuDocTools(h.api);

    const result = await h
      .tool("feishu_doc", { agentAccountId: "a" })
      .execute("call", { action: "list_blocks", doc_token: "doc-token" });
    expectRefused(result);
  });
});
