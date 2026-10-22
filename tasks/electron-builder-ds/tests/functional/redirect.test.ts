// Legitimate redirects keep working: credentials still reach the same origin (and the same host
// upgraded from http to https), other headers still follow, and requests complete.
import { readFileSync } from "node:fs"
import { CancellationToken } from "builder-util-runtime"
import { httpExecutor } from "builder-util"
import { afterEach, beforeEach, describe, expect, test } from "vitest"
import { resetNet, serve } from "../support/fakeElectron"
import { bytes, channelYaml, createUpdater, INSTALLER, LocalServer, NEW_VERSION, pathOf, serveBytes, sha512, startServer } from "../support/harness"

const FEED = "https://updates.example.test/feed/"
const CDN = "https://downloads.cdn-elsewhere.test"

beforeEach(() => resetNet())

describe("app updater (Electron net)", () => {
  test("full download through a redirect to another host completes with the right file", async () => {
    const file = bytes("full-cross", 5000)
    serve(FEED, req => {
      const p = pathOf(req)
      if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(file) }
      if (p.endsWith(`/${INSTALLER(NEW_VERSION)}`)) return { status: 302, headers: { location: `${CDN}/blobs/${INSTALLER(NEW_VERSION)}` } }
      return { status: 404 }
    })
    serve(CDN, req => serveBytes(req, file))

    const updater = createUpdater({ provider: "generic", url: FEED })
    updater.requestHeaders = { Authorization: "Bearer feed-token" }
    updater.disableDifferentialDownload = true
    await updater.checkForUpdates()
    const [downloaded] = await updater.downloadUpdate()
    expect(sha512(readFileSync(downloaded))).toBe(sha512(file))
  })

  test("full download through a redirect on the same server keeps the Authorization header", async () => {
    const file = bytes("full-same", 3000)
    serve(FEED, req => {
      const p = pathOf(req)
      if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(file) }
      if (p === `/feed/${INSTALLER(NEW_VERSION)}`) return { status: 302, headers: { location: `/storage/${INSTALLER(NEW_VERSION)}` } }
      if (p === `/storage/${INSTALLER(NEW_VERSION)}`) {
        return req.headers["authorization"] === "Bearer same-server-token" ? serveBytes(req, file) : { status: 401, body: "auth required" }
      }
      return { status: 404 }
    })

    const updater = createUpdater({ provider: "generic", url: FEED })
    updater.requestHeaders = { Authorization: "Bearer same-server-token" }
    updater.disableDifferentialDownload = true
    await updater.checkForUpdates()
    const [downloaded] = await updater.downloadUpdate()
    expect(sha512(readFileSync(downloaded))).toBe(sha512(file))
  })

  test("an http to https upgrade on the same host keeps the auth header", async () => {
    const HTTP_FEED = "http://updates.example.test/feed/"
    const HTTPS = "https://updates.example.test"
    const file = bytes("upgrade", 2048)
    serve(HTTP_FEED, req => {
      const p = pathOf(req)
      if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(file) }
      return { status: 301, headers: { location: `${HTTPS}${req.path}` } }
    })
    serve(HTTPS, req => (req.headers["authorization"] === "Bearer upgrade-token" ? serveBytes(req, file) : { status: 401, body: "auth required" }))

    const updater = createUpdater({ provider: "generic", url: HTTP_FEED })
    updater.addAuthHeader("Bearer upgrade-token")
    updater.disableDifferentialDownload = true
    await updater.checkForUpdates()
    const [downloaded] = await updater.downloadUpdate()
    expect(sha512(readFileSync(downloaded))).toBe(sha512(file))
  })

  test("a GitLab token-protected asset redirected within the server is still found", async () => {
    const GITLAB = "https://gitlab.example.test"
    const token = "glpat-samehosttoken"
    const yml = channelYaml(bytes("gitlab-installer", 1024))
    const release = (assetUrl: string) =>
      JSON.stringify({
        name: "Release v1.0.1",
        tag_name: "v1.0.1",
        description: "notes",
        created_at: "2026-01-01T00:00:00Z",
        released_at: "2026-01-01T00:00:00Z",
        upcoming_release: false,
        assets: { count: 1, sources: [], links: [{ id: 1, name: "latest-linux.yml", url: assetUrl, direct_asset_url: assetUrl, link_type: "other" }] },
      })
    serve(GITLAB, req => {
      if (req.headers["private-token"] !== token) return { status: 401, body: "{}" }
      const p = pathOf(req)
      if (p === "/api/v4/projects/42/releases/permalink/latest") return { status: 200, body: release(`${GITLAB}/-/project/42/uploads/bb22/latest-linux.yml`) }
      if (p === "/-/project/42/uploads/bb22/latest-linux.yml") return { status: 302, headers: { location: "/api/v4/projects/42/packages/generic/app/1.0.1/latest-linux.yml" } }
      if (p === "/api/v4/projects/42/packages/generic/app/1.0.1/latest-linux.yml") return { status: 200, body: yml }
      return { status: 404 }
    })
    const updater = createUpdater({ provider: "gitlab", host: "gitlab.example.test", projectId: 42, token })
    const result = await updater.checkForUpdates()
    expect(result?.updateInfo.version).toBe(NEW_VERSION)
  })
})

describe("publishing HTTP client (Node)", () => {
  let a: LocalServer
  let b: LocalServer
  afterEach(async () => {
    await a?.close()
    await b?.close()
  })

  test("a redirect on the same origin keeps Authorization and PRIVATE-TOKEN", async () => {
    a = await startServer(req => {
      if (req.url === "/old/releases") return { status: 302, headers: { location: "/new/releases" } }
      const ok = req.headers["authorization"] === "token same-origin-auth" && req.headers["private-token"] === "same-origin-private"
      return ok ? { status: 200, headers: { "content-type": "application/json" }, body: '{"ok":true}' } : { status: 401, body: "{}" }
    })
    const u = new URL("/old/releases", a.origin)
    const body = await httpExecutor.request(
      { protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname, headers: { Authorization: "token same-origin-auth", "PRIVATE-TOKEN": "same-origin-private" } },
      new CancellationToken()
    )
    expect(JSON.parse(body!)).toEqual({ ok: true })
  })

  test("a redirect to another origin completes and still sends the ordinary headers", async () => {
    b = await startServer(() => ({ status: 200, headers: { "content-type": "application/json" }, body: '{"moved":true}' }))
    a = await startServer(req => ({ status: 307, headers: { location: `${b.origin}/moved${req.url}` } }))
    const u = new URL("/api/releases", a.origin)
    const body = await httpExecutor.request(
      { protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname, headers: { Accept: "application/vnd.test+json", Authorization: "token cross-origin" } },
      new CancellationToken()
    )
    expect(JSON.parse(body!)).toEqual({ moved: true })
    const seen = b.seen[0].headers
    expect(seen["accept"]).toBe("application/vnd.test+json")
    expect(String(seen["user-agent"] ?? "")).not.toBe("")
  })

  test("a download redirected to another origin completes", async () => {
    const payload = "binary-payload-0123456789"
    b = await startServer(() => ({ status: 200, body: payload }))
    a = await startServer(req => ({ status: 302, headers: { location: `${b.origin}/blob${req.url}` } }))
    const buf = await httpExecutor.downloadToBuffer(new URL("/assets/app.zip", a.origin), {
      headers: { Authorization: "token dl" },
      cancellationToken: new CancellationToken(),
    })
    expect(buf.toString()).toBe(payload)
  })

  test("a download redirected on the same origin keeps the credential and completes", async () => {
    const payload = "same-origin-payload"
    a = await startServer(req => {
      if (req.url?.startsWith("/old/")) return { status: 302, headers: { location: "/new/asset.zip" } }
      return req.headers["authorization"] === "Bearer keep-me" ? { status: 200, body: payload } : { status: 401, body: "auth required" }
    })
    const buf = await httpExecutor.downloadToBuffer(new URL("/old/asset.zip", a.origin), {
      headers: { Authorization: "Bearer keep-me" },
      cancellationToken: new CancellationToken(),
    })
    expect(buf.toString()).toBe(payload)
  })
})
