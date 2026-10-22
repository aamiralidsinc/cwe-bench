/**
 * Shared verifier helpers. All expected values (address classification, marker text,
 * route tables) are computed here from the test's own data; no product helper is used
 * to decide whether an address is public or to clean up after a test.
 */
import { mkdtempSync } from "node:fs";
import { createServer as createNetServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { isIP } from "node:net";
import { expect } from "vitest";
import { runDaemonServer } from "@app/daemon-server";

export type StubCall = { url: string; method: string; redirect: string | null };
export type RouteValue =
  | Response
  | ((request: { url: string; method: string; init?: RequestInit }) => Response | Promise<Response>);

export interface FetchStub {
  impl: typeof fetch;
  calls: StubCall[];
}

export function makeFetch(routes: Record<string, RouteValue>): FetchStub {
  const calls: StubCall[] = [];
  const run = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const method = (
      init?.method ??
      (typeof input !== "string" && !(input instanceof URL) ? input.method : "GET")
    ).toUpperCase();
    calls.push({ url, method, redirect: init?.redirect ?? null });
    const route = routes[url];
    if (!route) return new Response("not found", { status: 404 });
    const raw = typeof route === "function" ? await route({ url, method, init }) : route;
    const res = raw instanceof Response ? raw : new Response(raw.body ?? null, raw);
    const location = res.headers.get("location");
    if (res.status >= 300 && res.status < 400 && location && (init?.redirect ?? "follow") === "follow") {
      return await run(new URL(location, url).href, { ...init, redirect: "follow" });
    }
    return res;
  };
  return { impl: run as unknown as typeof fetch, calls };
}

export function html(body: string): Response {
  return new Response(body, { status: 200, headers: { "content-type": "text/html" } });
}

export function feedXml(body: string): Response {
  return new Response(body, { status: 200, headers: { "content-type": "application/rss+xml" } });
}

export function vtt(body: string): Response {
  return new Response(body, { status: 200, headers: { "content-type": "text/vtt" } });
}

export function json(value: unknown): Response {
  return new Response(JSON.stringify(value), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

export function redirectTo(location: string): Response {
  return new Response(null, { status: 302, headers: { location } });
}

export function rss(inner: string): string {
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:podcast="https://podcastindex.org/namespace/1.0"><channel><title>Show</title><item><title>Episode 1</title>${inner}</item></channel></rss>`;
}

export const TRANSCRIPT_MARKER = "public-transcript-marker";
export const CAPTION_MARKER = "public-caption-marker";
export const SPOTIFY_MARKER = "public-spotify-marker";

export const VTT_BODY = (marker: string) =>
  `WEBVTT\n\n00:00:00.000 --> 00:00:02.000\n${marker}\n`;

export const FEED_URL = "https://feed.summarize-test.example/feed.xml";
export const PAGE_URL = "https://page.summarize-test.example/article";

/** Internal destinations used by the security tests. */
export const INTERNAL = {
  loopback: "http://127.0.0.1:9/internal/transcript.vtt",
  ula: "http://[fd00::1]/internal/transcript.vtt",
  metadata: "http://169.254.169.254/latest/meta-data/",
  privateName: "http://internal.summarize-test.example/internal/transcript.vtt",
  privateTen: "http://10.1.2.3/internal/transcript.vtt",
  nat64Loopback: "http://[64:ff9b::7f00:1]:8080/internal",
  sixToFourLoopback: "http://[2002:7f00:1::]:8080/internal",
  unresolvable: "http://unresolvable.summarize-test.example/internal/transcript.vtt",
  chapters: "http://127.0.0.1:9/internal/chapters.json",
  spotify: "http://127.0.0.1:9/internal/spotify.vtt",
} as const;

/** Public destinations used by the functional tests. */
export const PUBLIC = {
  transcriptName: "https://cdn.summarize-test.example/transcript.vtt",
  transcriptSecondHop: "https://transcript.summarize-test.example/transcript.vtt",
  transcriptLiteral: "https://93.184.216.34/transcript.vtt",
  caption: "https://cdn.summarize-test.example/captions.vtt",
  enclosure: "https://media.summarize-test.example/episode.mp3",
  chapters: "https://chapters.summarize-test.example/chapters.json",
  spotifyTranscript: "https://cdn.summarize-test.example/spotify.vtt",
  daemonNat64: "http://[64:ff9b::808:808]:8080/article",
} as const;

const PUBLIC_NAMES = new Set(
  [
    "feed.summarize-test.example",
    "page.summarize-test.example",
    "cdn.summarize-test.example",
    "media.summarize-test.example",
    "chapters.summarize-test.example",
    "transcript.summarize-test.example",
    "open.spotify.com",
    "example.com",
    "cdn.example.com",
    "itunes.apple.com",
    "podcasts.apple.com",
    "scdn.co",
    "audio4-fa.scdn.co",
    "example.org",
    "insecure.example.com",
    "api.openai.com",
    "api.groq.com",
    "api.assemblyai.com",
  ].map((name) => name.toLowerCase()),
);

function parseIpv4(address: string): number[] | null {
  const parts = address.split(".");
  if (parts.length !== 4) return null;
  const octets = parts.map((part) => (/^\d{1,3}$/.test(part) ? Number(part) : NaN));
  return octets.every((value) => Number.isInteger(value) && value >= 0 && value <= 255)
    ? octets
    : null;
}

function isPublicIpv4(address: string): boolean {
  const octets = parseIpv4(address);
  if (!octets) return false;
  const [a, b] = octets;
  if (a === 0 || a === 10 || a === 127) return false;
  if (a === 100 && b >= 64 && b <= 127) return false;
  if (a === 169 && b === 254) return false;
  if (a === 172 && b >= 16 && b <= 31) return false;
  if (a === 192 && b === 168) return false;
  if (a === 192 && b === 0) return false;
  if (a === 198 && (b === 18 || b === 19)) return false;
  if (a === 198 && b === 51 && octets[2] === 100) return false;
  if (a === 203 && b === 0 && octets[2] === 113) return false;
  if (a >= 224) return false;
  return true;
}

function expandIpv6(address: string): number[] | null {
  const normalized = address.split("%", 1)[0]?.toLowerCase() ?? "";
  if (!normalized) return null;
  const mapped = normalized.match(/^(.*:)(\d{1,3}(?:\.\d{1,3}){3})$/);
  const ipv4 = mapped ? parseIpv4(mapped[2] ?? "") : null;
  const head = mapped ? (mapped[1] ?? "") : normalized;
  const groups = head.split("::");
  if (groups.length > 2) return null;
  const [leftRaw, rightRaw] = groups;
  const left = leftRaw ? leftRaw.split(":").filter(Boolean) : [];
  const right = rightRaw ? rightRaw.split(":").filter(Boolean) : [];
  const ipv4Parts = ipv4
    ? [((ipv4[0] ?? 0) << 8) | (ipv4[1] ?? 0), ((ipv4[2] ?? 0) << 8) | (ipv4[3] ?? 0)]
    : [];
  const missing = 8 - left.length - right.length - ipv4Parts.length;
  if (missing < 0 || (groups.length === 1 && missing !== 0)) return null;
  const toPart = (part: string) => (/^[0-9a-f]{1,4}$/.test(part) ? parseInt(part, 16) : -1);
  const parts = [
    ...left.map(toPart),
    ...Array.from({ length: missing }, () => 0),
    ...right.map(toPart),
    ...ipv4Parts,
  ];
  return parts.length === 8 && parts.every((part) => part >= 0 && part <= 0xffff) ? parts : null;
}

function embeddedIpv4(parts: number[]): string {
  const sixth = parts[6] ?? 0;
  const eighth = parts[7] ?? 0;
  return `${(sixth >> 8) & 0xff}.${sixth & 0xff}.${(eighth >> 8) & 0xff}.${eighth & 0xff}`;
}

function isPublicIpv6(address: string): boolean {
  const parts = expandIpv6(address);
  if (!parts) return false;
  const [first, second, third, fourth] = parts;
  const allZero = parts.every((part) => part === 0);
  const loopback = parts.slice(0, 7).every((part) => part === 0) && parts[7] === 1;
  const mapped = parts.slice(0, 5).every((part) => part === 0) && parts[5] === 0xffff;
  const compatible = parts.slice(0, 6).every((part) => part === 0) && !allZero && !loopback;
  if (mapped || compatible) return isPublicIpv4(embeddedIpv4(parts));
  const nat64 = first === 0x64 && second === 0xff9b && parts.slice(2, 6).every((part) => part === 0);
  if (nat64) return isPublicIpv4(embeddedIpv4(parts));
  if (allZero || loopback) return false;
  if (first === 0x64 && second === 0xff9b && third === 1) return false;
  if (first === 0x100 && second === 0 && third === 0 && fourth === 0) return false;
  if ((first & 0xfe00) === 0xfc00) return false;
  if ((first & 0xffc0) === 0xfe80) return false;
  if ((first & 0xff00) === 0xff00) return false;
  if (first === 0x2001 && second <= 0x01ff) return false;
  if (first === 0x2001 && second === 0xdb8) return false;
  if (first === 0x2002) return false;
  if (first === 0x3fff && second <= 0x0fff) return false;
  if (first === 0x5f00) return false;
  return true;
}

/** True when the URL points anywhere other than a public internet destination. */
export function isNonPublicUrl(rawUrl: string): boolean {
  let url: URL;
  try {
    url = new URL(rawUrl);
  } catch {
    return true;
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return true;
  const hostname = url.hostname.trim().replace(/^\[|\]$/g, "").toLowerCase();
  if (hostname === "localhost" || hostname.endsWith(".localhost")) return true;
  const family = isIP(hostname);
  if (family === 4) return !isPublicIpv4(hostname);
  if (family === 6) return !isPublicIpv6(hostname);
  return !PUBLIC_NAMES.has(hostname);
}

export function nonPublicCalls(stub: FetchStub): StubCall[] {
  return stub.calls.filter((call) => isNonPublicUrl(call.url));
}

/** Assert that the product never asked its transport for a non-public destination. */
export function expectNoNonPublicFetch(stub: FetchStub): void {
  expect(nonPublicCalls(stub)).toEqual([]);
}

export function called(stub: FetchStub, url: string): boolean {
  return stub.calls.some((call) => call.url === url);
}

export async function findFreePort(): Promise<number> {
  return await new Promise((resolve, reject) => {
    const server = createNetServer();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        server.close(() => reject(new Error("Failed to resolve port")));
        return;
      }
      const { port } = address;
      server.close((error) => (error ? reject(error) : resolve(port)));
    });
  });
}

export interface DaemonHandle {
  port: number;
  token: string;
  close(): Promise<void>;
}

export async function startDaemon(stub: FetchStub): Promise<DaemonHandle> {
  const home = mkdtempSync(join(tmpdir(), "summarize-verifier-daemon-"));
  const port = await findFreePort();
  const token = "verifier-daemon-token-0123456789";
  const abortController = new AbortController();
  let resolveReady: (() => void) | null = null;
  const ready = new Promise<void>((resolve) => {
    resolveReady = resolve;
  });
  const serverPromise = runDaemonServer({
    env: { HOME: home },
    fetchImpl: stub.impl,
    config: { token, port, version: 1, installedAt: new Date().toISOString() },
    port,
    signal: abortController.signal,
    onListening: () => resolveReady?.(),
  });
  await ready;
  return {
    port,
    token,
    async close() {
      abortController.abort();
      await Promise.race([
        serverPromise.catch(() => undefined),
        new Promise<void>((resolve) => setTimeout(resolve, 5000)),
      ]);
    },
  };
}

export async function postSummarize(
  daemon: DaemonHandle,
  url: string,
): Promise<{ status: number; body: unknown }> {
  const res = await fetch(`http://127.0.0.1:${daemon.port}/v1/summarize`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${daemon.token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ url, mode: "url", extractOnly: true }),
  });
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  return { status: res.status, body };
}
