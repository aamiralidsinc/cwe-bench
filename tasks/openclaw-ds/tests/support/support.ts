// Shared support for the hidden Feishu suites: a minimal stand-in for the plugin
// registration API and the configuration shapes the tests drive. Kept test-local so a
// hardened product helper cannot change what the tests expect.
import type { OpenClawPluginApi } from "../../runtime-api.js";

export type ToolResult = { details?: Record<string, unknown> };

export type RegisteredTool = {
  name: string;
  execute: (toolCallId: string, params: unknown) => Promise<ToolResult>;
};

export type ToolHarness = {
  api: OpenClawPluginApi;
  tool: (name: string, ctx?: Record<string, unknown>) => RegisteredTool;
  names: () => string[];
};

export function createToolHarness(cfg: OpenClawPluginApi["config"]): ToolHarness {
  const registered: { name: string; tool: unknown }[] = [];
  const api = {
    config: cfg,
    logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
    registerTool: (tool: unknown, opts?: { name?: string }) => {
      const name = opts?.name ?? (tool as { name?: string } | undefined)?.name;
      if (!name) {
        throw new Error("registered tool without a name");
      }
      registered.push({ name, tool });
    },
  } as unknown as OpenClawPluginApi;

  const tool = (name: string, ctx: Record<string, unknown> = {}): RegisteredTool => {
    const entry = registered.find((candidate) => candidate.name === name);
    if (!entry) {
      throw new Error(`tool not registered: ${name}`);
    }
    const resolved =
      typeof entry.tool === "function"
        ? (entry.tool as (context: unknown) => unknown)(ctx)
        : entry.tool;
    const candidate = resolved as Partial<RegisteredTool>;
    if (typeof candidate.execute !== "function") {
      throw new Error(`tool has no execute: ${name}`);
    }
    return { name, execute: (id, params) => candidate.execute!(id, params) };
  };

  return { api, tool, names: () => registered.map((entry) => entry.name) };
}

export function twoAccounts(
  toolsA: Record<string, unknown> | undefined,
  toolsB: Record<string, unknown> | undefined,
  extra: { topTools?: Record<string, unknown>; defaultAccount?: string } = {},
): OpenClawPluginApi["config"] {
  return {
    channels: {
      feishu: {
        enabled: true,
        defaultAccount: extra.defaultAccount,
        tools: extra.topTools,
        accounts: {
          a: { appId: "app-a", appSecret: "sec-a", tools: toolsA },
          b: { appId: "app-b", appSecret: "sec-b", tools: toolsB },
        },
      },
    },
  } as unknown as OpenClawPluginApi["config"];
}

export function hasError(result: ToolResult): boolean {
  const details = result?.details ?? {};
  return typeof details.error === "string" && details.error.length > 0;
}

export function errorText(result: ToolResult): string {
  const details = result?.details ?? {};
  return typeof details.error === "string" ? details.error : "";
}
