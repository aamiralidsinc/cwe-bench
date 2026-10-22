/**
 * Shared verifier helpers: real MCP client over an in-memory transport, and
 * local canaries that record whether anything actually connected to an
 * internal address.
 */
import http from "node:http";
import net from "node:net";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createServer, registerAll } from "../src/server";

export interface Canary {
  port: number;
  readonly hits: number;
  close(): Promise<void>;
}

export async function startHttpCanary(
  respond: (req: http.IncomingMessage, res: http.ServerResponse) => void
): Promise<Canary> {
  let hits = 0;
  const server = http.createServer((req, res) => {
    hits += 1;
    respond(req, res);
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const port = (server.address() as net.AddressInfo).port;
  return {
    port,
    get hits() {
      return hits;
    },
    close: () => new Promise<void>((resolve) => server.close(() => resolve()))
  };
}

export async function startTcpCanary(port = 0): Promise<Canary> {
  let hits = 0;
  const server = net.createServer((socket) => {
    hits += 1;
    socket.destroy();
  });
  await new Promise<void>((resolve) => server.listen(port, "127.0.0.1", () => resolve()));
  const bound = (server.address() as net.AddressInfo).port;
  return {
    port: bound,
    get hits() {
      return hits;
    },
    close: () => new Promise<void>((resolve) => server.close(() => resolve()))
  };
}

export function ckanJson(body: unknown): (req: http.IncomingMessage, res: http.ServerResponse) => void {
  return (_req, res) => {
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify(body));
  };
}

export function textResponse(contentType: string, body: string) {
  return (_req: http.IncomingMessage, res: http.ServerResponse) => {
    res.setHeader("content-type", contentType);
    res.end(body);
  };
}

export interface McpHandle {
  client: Client;
  close(): Promise<void>;
}

export async function connectMcp(): Promise<McpHandle> {
  const server = createServer();
  registerAll(server);
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "verifier", version: "1.0.0" }, { capabilities: {} });
  await Promise.all([server.connect(serverTransport), client.connect(clientTransport)]);
  return {
    client,
    async close() {
      await client.close();
      await server.close();
    }
  };
}

export interface ToolResult {
  isError?: boolean;
  content?: Array<{ type: string; text?: string }>;
  structuredContent?: unknown;
  protocolError?: unknown;
}

/** Call a tool; a transport-level rejection also counts as a client-visible error. */
export async function callTool(
  client: Client,
  name: string,
  args: Record<string, unknown>
): Promise<ToolResult> {
  try {
    const result = (await client.callTool({ name, arguments: args })) as ToolResult;
    return result;
  } catch (error) {
    return { isError: true, protocolError: error };
  }
}

export function resultText(result: ToolResult): string {
  return (result.content ?? [])
    .map((entry) => (typeof entry.text === "string" ? entry.text : ""))
    .join("\n");
}

export function refusalReported(result: ToolResult): boolean {
  return result.isError === true || result.protocolError !== undefined;
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function pickFreePort(): Promise<number> {
  const server = net.createServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const port = (server.address() as net.AddressInfo).port;
  await new Promise<void>((resolve) => server.close(() => resolve()));
  return port;
}

export async function portAccepts(port: number, timeoutMs = 500): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.connect({ port, host: "127.0.0.1" });
    const done = (value: boolean) => {
      socket.destroy();
      resolve(value);
    };
    socket.setTimeout(timeoutMs, () => done(false));
    socket.once("connect", () => done(true));
    socket.once("error", () => done(false));
  });
}
