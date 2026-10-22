// Test helpers. Expected values and clean-ups are computed here with Node built-ins only, never
// with product code.
import { createHash } from "node:crypto"
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs"
import { createServer, IncomingMessage, Server } from "node:http"
import { AddressInfo } from "node:net"
import { tmpdir } from "node:os"
import * as path from "node:path"
import { gzipSync } from "node:zlib"
import { NsisUpdater } from "electron-updater/out/NsisUpdater"
import { FakeResponse, SeenRequest, seenRequests, setAppInfo } from "./fakeElectron"

export const OLD_VERSION = "1.0.0"
export const NEW_VERSION = "1.0.1"
export const INSTALLER = (v: string) => `credential-test-app-Setup-${v}.exe`

let counter = 0
export function tempDir(prefix: string): string {
  return mkdtempSync(path.join(tmpdir(), `cwe-${prefix}-`))
}

/** Every header value any origin other than `allowed` received, across all requests so far. */
export function headersSeenOutside(allowed: string): Array<SeenRequest> {
  const keep = new URL(allowed).origin
  return seenRequests().filter(r => r.origin !== keep)
}

export function anyHeaderContains(reqs: Array<SeenRequest>, marker: string): Array<string> {
  const hits: Array<string> = []
  for (const r of reqs) {
    for (const [k, v] of Object.entries(r.headers)) {
      if (k.includes(marker.toLowerCase()) || v.includes(marker)) {
        hits.push(`${r.origin}${r.path} ${k}`)
      }
    }
  }
  return hits
}

export function sha512(buf: Buffer): string {
  return createHash("sha512").update(buf).digest("base64")
}

/** Deterministic pseudo-random bytes. */
export function bytes(seed: string, length: number): Buffer {
  const out = Buffer.alloc(length)
  let block = createHash("sha256").update(seed).digest()
  for (let i = 0; i < length; i++) {
    if (i % 32 === 0 && i > 0) {
      block = createHash("sha256").update(block).digest()
    }
    out[i] = block[i % 32]
  }
  return out
}

export const BLOCK = 256

/** A blockmap (format version 2) for `buf` with fixed-size blocks, gzipped as served. */
export function blockMap(buf: Buffer): Buffer {
  const checksums: Array<string> = []
  const sizes: Array<number> = []
  for (let off = 0; off < buf.length; off += BLOCK) {
    const chunk = buf.subarray(off, Math.min(buf.length, off + BLOCK))
    checksums.push(createHash("sha256").update(chunk).digest("base64"))
    sizes.push(chunk.length)
  }
  return gzipSync(JSON.stringify({ version: "2", files: [{ name: "file", offset: 0, checksums, sizes }] }))
}

/** Old and new installers that differ in two separate blocks, so a differential download needs two ranges. */
export function installerPair(): { oldFile: Buffer; newFile: Buffer } {
  const oldFile = bytes("old-installer", BLOCK * 8)
  const newFile = Buffer.from(oldFile)
  bytes("changed-1", BLOCK).copy(newFile, BLOCK * 2)
  bytes("changed-2", BLOCK).copy(newFile, BLOCK * 6)
  return { oldFile, newFile }
}

export function channelYaml(file: Buffer, url = INSTALLER(NEW_VERSION)): string {
  const hash = sha512(file)
  return [
    `version: ${NEW_VERSION}`,
    "files:",
    `  - url: ${url}`,
    `    sha512: ${hash}`,
    `    size: ${file.length}`,
    `path: ${url}`,
    `sha512: ${hash}`,
    "releaseDate: '2026-01-01T00:00:00.000Z'",
    "",
  ].join("\n")
}

/** Serves `buf`, honouring a single `Range: bytes=a-b` request header. */
export function serveBytes(req: SeenRequest, buf: Buffer): FakeResponse {
  const range = req.headers["range"]
  if (range != null) {
    const m = /^bytes=(\d+)-(\d+)$/.exec(range.trim())
    if (m == null) {
      return { status: 416 }
    }
    const start = Number(m[1])
    const end = Number(m[2])
    return {
      status: 206,
      headers: { "content-range": `bytes ${start}-${end}/${buf.length}`, "accept-ranges": "bytes" },
      body: buf.subarray(start, end + 1),
    }
  }
  return { status: 200, headers: { "accept-ranges": "bytes" }, body: buf }
}

export function pathOf(req: SeenRequest): string {
  return req.path.split("?")[0]
}

/**
 * An updater configured the way a packaged app is (Electron app adapter and Electron `net`), with
 * its own config file, user-data and cache directories. `oldInstaller` is put where the updater
 * keeps the currently installed version's installer, enabling differential downloads.
 */
export function createUpdater(publish: Record<string, unknown>, oldInstaller?: Buffer): NsisUpdater {
  const root = tempDir("updater")
  const cacheDirName = `credential-test-app-updater-${process.pid}-${++counter}`
  const configPath = path.join(root, "app-update.yml")
  const lines = [`updaterCacheDirName: ${cacheDirName}`]
  for (const [k, v] of Object.entries(publish)) {
    lines.push(`${k}: ${typeof v === "string" ? JSON.stringify(v) : String(v)}`)
  }
  writeFileSync(configPath, lines.join("\n") + "\n")

  const userData = path.join(root, "userData")
  const cache = path.join(root, "cache")
  mkdirSync(userData, { recursive: true })
  mkdirSync(path.join(cache, cacheDirName), { recursive: true })
  if (oldInstaller != null) {
    writeFileSync(path.join(cache, cacheDirName, "installer.exe"), oldInstaller)
  }
  process.env.XDG_CACHE_HOME = cache
  setAppInfo(OLD_VERSION, userData)

  const updater = new NsisUpdater()
  updater.updateConfigPath = configPath
  updater.logger = null
  updater.autoDownload = false
  updater.autoInstallOnAppQuit = false
  return updater
}

export interface LocalServer {
  origin: string
  seen: Array<{ path: string; headers: IncomingMessage["headers"] }>
  close: () => Promise<void>
}

export type LocalHandler = (req: IncomingMessage, body: string) => { status: number; headers?: Record<string, string>; body?: string }

/** A plain HTTP server on 127.0.0.1 (each server has its own port, so its own origin). */
export async function startServer(handler: LocalHandler): Promise<LocalServer> {
  const seen: LocalServer["seen"] = []
  const server: Server = createServer((req, res) => {
    let body = ""
    req.on("data", c => (body += c))
    req.on("end", () => {
      seen.push({ path: req.url ?? "/", headers: { ...req.headers } })
      const r = handler(req, body)
      res.writeHead(r.status, r.headers ?? {})
      res.end(r.body ?? "")
    })
  })
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve))
  const port = (server.address() as AddressInfo).port
  return {
    origin: `http://127.0.0.1:${port}`,
    seen,
    close: () => new Promise<void>(resolve => server.close(() => resolve())),
  }
}

export function localHeadersContain(seen: LocalServer["seen"], marker: string): Array<string> {
  const hits: Array<string> = []
  for (const r of seen) {
    for (const [k, v] of Object.entries(r.headers)) {
      const value = Array.isArray(v) ? v.join(", ") : String(v ?? "")
      if (value.includes(marker)) {
        hits.push(`${r.path} ${k}`)
      }
    }
  }
  return hits
}
