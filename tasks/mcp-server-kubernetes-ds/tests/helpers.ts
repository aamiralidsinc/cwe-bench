/**
 * Shared verifier helpers.
 *
 * Every test drives the product the way a client does: the built MCP server is
 * started as a child process and spoken to over the standard MCP stdio
 * transport. `kubectl` and `helm` are replaced by stand-ins first on PATH that
 * record the argv they were handed and answer with fixed output, so a test can
 * see exactly what would have been executed without a cluster.
 *
 * The argv recorded for a stand-in is parsed the way pflag parses it: a bare
 * "--" ends the option list, long options end at "=", and a single-dash token
 * is a cluster of short options whose walk stops at the first option that
 * takes a value.
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { expect } from "vitest";

export const WORKSPACE = process.env.WORKSPACE_DIR || "/workspace";

const DANGEROUS_LONG = new Set<string>([
  "server",
  "kubeconfig",
  "cluster",
  "user",
  "tls-server-name",
  "insecure-skip-tls-verify",
  "certificate-authority",
  "client-certificate",
  "client-key",
  "token",
  "username",
  "password",
  "auth-provider",
  "auth-provider-arg",
  "exec-command",
  "exec-arg",
  "exec-api-version",
  "exec-env",
  "as",
  "as-group",
  "as-uid",
  "kube-apiserver",
  "kube-token",
  "kube-ca-file",
  "kube-as-user",
  "kube-as-group",
  "kube-tls-server-name",
  "kube-insecure-skip-tls-verify",
]);
const CONTEXT_LONG = new Set<string>(["context", "kube-context"]);
const SHORT_VALUE_FLAGS = new Set<string>(["c", "k", "l", "L", "n", "o", "s", "v"]);

/** Tokens in one recorded argv that the binary would read as a protected option. */
export function dangerousTokens(argv: string[]): string[] {
  const bad: string[] = [];
  for (const tok of argv) {
    if (typeof tok !== "string") continue;
    if (tok === "--") break;
    if (!tok.startsWith("-")) continue;

    if (tok.startsWith("--")) {
      const name = tok.slice(2).split("=")[0].toLowerCase().replace(/_/g, "-");
      if (name && !CONTEXT_LONG.has(name) && DANGEROUS_LONG.has(name)) bad.push(tok);
      continue;
    }

    const body = tok.slice(1);
    for (let i = 0; i < body.length; i++) {
      const letter = body[i];
      if (letter === "s") {
        bad.push(tok);
        break;
      }
      if (body[i + 1] === "=") break;
      if (SHORT_VALUE_FLAGS.has(letter)) break;
    }
  }
  return bad;
}

const FAKE_KUBECTL = `#!/bin/bash
{
  for a in "$@"; do printf '%s\\034' "$a"; done
  printf '\\n'
} >> "\${KUBECTL_LOG}"
joined=" $* "
case "$joined" in
  *"config get-contexts"*)
    if [[ "$joined" == *"-o name"* ]]; then
      printf 'ctx\\n--server=https://attacker.example/ctx\\n'
    else
      printf 'CURRENT   NAME   CLUSTER   AUTHINFO   NAMESPACE\\n'
      printf '*         ctx    c         u          default\\n'
      printf '          --server=https://attacker.example/ctx   c   u   default\\n'
    fi
    ;;
  *"config current-context"*) printf 'ctx\\n' ;;
  *" get node "*) printf '{"spec":{"unschedulable":false}}\\n' ;;
  *" get jobs "*) printf 'pod-a\\n' ;;
  *" get "*|*" describe "*) printf '{"kind":"PodList","items":[]}\\n' ;;
  *" logs "*) printf 'hello from pod\\n' ;;
  *" explain "*) printf 'RESOURCE: pods\\n' ;;
  *" api-resources "*) printf 'NAME SHORTNAMES\\npods po\\n' ;;
  *" port-forward "*) printf 'Forwarding from 127.0.0.1:18080 -> 8080\\n' ;;
  *) printf 'ok\\n' ;;
esac
exit 0
`;

const FAKE_HELM = `#!/bin/bash
{
  for a in "$@"; do printf '%s\\034' "$a"; done
  printf '\\n'
} >> "\${HELM_LOG}"
joined=" $* "
case "$joined" in
  *" template "*) printf 'apiVersion: v1\\nkind: List\\nitems: []\\n' ;;
  *) printf 'ok\\n' ;;
esac
exit 0
`;

const KUBECONFIG_YAML = `apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://127.0.0.1:1
    insecure-skip-tls-verify: true
  name: c
users:
- name: u
  user:
    token: dummy
contexts:
- context:
    cluster: c
    user: u
    namespace: default
  name: ctx
current-context: ctx
`;

export interface ToolOutcome {
  /** Raw result when the MCP call returned one. */
  result?: { isError?: boolean; content?: Array<{ type: string; text?: string }> };
  /** Text of the result content. */
  text: string;
  /** Transport-level rejection reported to the client. */
  error?: string;
  /** The request was reported to the client as a failure. */
  refused: boolean;
}

export interface ResourceOutcome {
  contents?: Array<{ uri?: string; mimeType?: string; text?: string }>;
  error?: string;
  refused: boolean;
}

export interface ServerHandle {
  readonly dir: string;
  callTool(name: string, args: Record<string, unknown>): Promise<ToolOutcome>;
  readResource(uri: string): Promise<ResourceOutcome>;
  /** Every argv the kubectl stand-in was given since the last reset. */
  kubectl(): string[][];
  /** Every argv the helm stand-in was given since the last reset. */
  helm(): string[][];
  /** Protected options found in any recorded argv. */
  dangerous(): string[];
  reset(): void;
  close(): Promise<void>;
}

function readArgv(file: string): string[][] {
  if (!fs.existsSync(file)) return [];
  return fs
    .readFileSync(file, "utf8")
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => line.split("\u001c").filter((token) => token.length > 0));
}

function resultText(result: { content?: Array<{ type: string; text?: string }> }): string {
  return (result.content ?? [])
    .map((entry) => (typeof entry.text === "string" ? entry.text : ""))
    .join("\n");
}

function reportsFailure(text: string): boolean {
  return (
    /"status"\s*:\s*"failed"/.test(text) ||
    /"success"\s*:\s*false/.test(text) ||
    /"error"\s*:/.test(text)
  );
}

export async function startServer(): Promise<ServerHandle> {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "k8s-mcp-"));
  const binDir = path.join(dir, "bin");
  fs.mkdirSync(binDir);
  fs.writeFileSync(path.join(binDir, "kubectl"), FAKE_KUBECTL, { mode: 0o755 });
  fs.writeFileSync(path.join(binDir, "helm"), FAKE_HELM, { mode: 0o755 });
  fs.writeFileSync(path.join(dir, "kubeconfig.yaml"), KUBECONFIG_YAML);

  const kubectlLog = path.join(dir, "kubectl.log");
  const helmLog = path.join(dir, "helm.log");

  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [path.join(WORKSPACE, "dist", "index.js")],
    cwd: WORKSPACE,
    env: {
      PATH: `${binDir}:/usr/local/bin:/usr/bin:/bin`,
      HOME: process.env.HOME || "/home/agent",
      LANG: "C.UTF-8",
      LC_ALL: "C.UTF-8",
      TZ: "UTC",
      KUBECONFIG: path.join(dir, "kubeconfig.yaml"),
      KUBECTL_LOG: kubectlLog,
      HELM_LOG: helmLog,
      ENABLE_TELEMETRY: "false",
    },
    stderr: "pipe",
  });
  const client = new Client({ name: "verifier", version: "1.0.0" }, { capabilities: {} });
  // Drain the child's stderr so a chatty start-up can never fill the pipe.
  transport.stderr?.on("data", () => undefined);
  await client.connect(transport);

  const handle: ServerHandle = {
    dir,
    async callTool(name, args) {
      try {
        const result = (await client.callTool({ name, arguments: args })) as ToolOutcome["result"];
        const text = resultText(result ?? {});
        return { result, text, refused: result?.isError === true || reportsFailure(text) };
      } catch (error) {
        return { text: "", error: String(error), refused: true };
      }
    },
    async readResource(uri) {
      try {
        const result = (await client.readResource({ uri })) as {
          contents?: Array<{ uri?: string; mimeType?: string; text?: string }>;
        };
        return { contents: result.contents ?? [], refused: false };
      } catch (error) {
        return { error: String(error), refused: true };
      }
    },
    kubectl: () => readArgv(kubectlLog),
    helm: () => readArgv(helmLog),
    dangerous: () => [...readArgv(kubectlLog), ...readArgv(helmLog)].flatMap(dangerousTokens),
    reset() {
      for (const file of [kubectlLog, helmLog]) {
        try {
          fs.rmSync(file);
        } catch {
          // not created yet
        }
      }
    },
    async close() {
      try {
        await client.close();
      } finally {
        fs.rmSync(dir, { recursive: true, force: true });
      }
    },
  };
  return handle;
}

/**
 * Assert that an attempted request was blocked: no protected option reached a
 * command line, the client was told the request failed, and the server is
 * still able to serve an unrelated request (a process that dies instead of
 * refusing is not a clean refusal).
 */
export async function expectBlocked(server: ServerHandle, outcome: { refused: boolean }): Promise<void> {
  expect(server.dangerous(), "no protected option may reach a command line").toEqual([]);
  expect(outcome.refused, "the refused request must be reported to the client").toBe(true);
  const ping = await server.callTool("ping", {});
  expect(ping.refused, "the server must keep serving after a refusal").toBe(false);
}
