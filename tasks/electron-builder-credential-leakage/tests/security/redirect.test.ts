// Credentials attached to a request must not reach another origin when the server redirects.
// Each test asserts only on what the other origin received; refusing the request is also fine.
import { CancellationToken } from "builder-util-runtime"
import { httpExecutor } from "builder-util"
import { afterEach, beforeEach, describe, expect, test } from "vitest"
import { resetNet, serve } from "../support/fakeElectron"
import {
  anyHeaderContains,
  bytes,
  channelYaml,
  createUpdater,
  headersSeenOutside,
  INSTALLER,
  localHeadersContain,
  LocalServer,
  NEW_VERSION,
  pathOf,
  serveBytes,
  startServer,
} from "../support/harness"

const FEED = "https://updates.example.test/feed/"
const CDN = "https://downloads.cdn-elsewhere.test"

beforeEach(() => resetNet())

describe("app updater (Electron net)", () => {
  test("full download: a capitalised Authorization request header is not sent to the redirect target on another host", async () => {
    const MARK = "UPDATERAUTHMARK7731"
    const file = bytes("full-download", 4096)
    serve(FEED, req => {
      const p = pathOf(req)
      if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(file) }
      if (p.endsWith(`/${INSTALLER(NEW_VERSION)}`)) return { status: 302, headers: { location: `${CDN}/blobs/${INSTALLER(NEW_VERSION)}` } }
      return { status: 404 }
    })
    serve(CDN, req => serveBytes(req, file))

    const updater = createUpdater({ provider: "generic", url: FEED })
    updater.requestHeaders = { Authorization: `Bearer ${MARK}` }
    updater.disableDifferentialDownload = true
    await updater.checkForUpdates()
    await updater.downloadUpdate().catch(() => null)

    expect(anyHeaderContains(headersSeenOutside(FEED), MARK)).toEqual([])
  })

  test("GitLab provider: the project access token is not sent to object storage the asset link redirects to", async () => {
    const MARK = "GLPATTOKENMARK4410"
    const GITLAB = "https://gitlab.example.test"
    const STORAGE = "https://objects.storage-elsewhere.test"
    const yml = channelYaml(bytes("gitlab-installer", 1024))
    serve(GITLAB, req => {
      const p = pathOf(req)
      if (p === "/api/v4/projects/42/releases/permalink/latest") {
        return {
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            name: "Release v1.0.1",
            tag_name: "v1.0.1",
            description: "notes",
            created_at: "2026-01-01T00:00:00Z",
            released_at: "2026-01-01T00:00:00Z",
            upcoming_release: false,
            assets: {
              count: 1,
              sources: [],
              links: [
                {
                  id: 1,
                  name: "latest-linux.yml",
                  url: `${GITLAB}/-/project/42/uploads/aa11/latest-linux.yml`,
                  direct_asset_url: `${GITLAB}/-/project/42/uploads/aa11/latest-linux.yml`,
                  link_type: "other",
                },
              ],
            },
          }),
        }
      }
      if (p === "/-/project/42/uploads/aa11/latest-linux.yml") {
        return { status: 302, headers: { location: `${STORAGE}/bucket/aa11/latest-linux.yml?sig=1` } }
      }
      return { status: 404 }
    })
    serve(STORAGE, () => ({ status: 200, body: yml }))

    const updater = createUpdater({ provider: "gitlab", host: "gitlab.example.test", projectId: 42, token: `glpat-${MARK}` })
    await updater.checkForUpdates().catch(() => null)

    expect(anyHeaderContains(headersSeenOutside(GITLAB), MARK)).toEqual([])
  })
})

describe("publishing HTTP client (Node)", () => {
  let a: LocalServer
  let b: LocalServer
  beforeEach(async () => {
    b = await startServer(() => ({ status: 200, headers: { "content-type": "application/json" }, body: "{}" }))
    a = await startServer(req => ({ status: 307, headers: { location: `${b.origin}/moved${req.url}` } }))
  })
  afterEach(async () => {
    await a.close()
    await b.close()
  })

  const opts = (path: string, headers: Record<string, string>) => {
    const u = new URL(path, a.origin)
    return { protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname, headers }
  }

  test("API request: API-key, cookie and proxy credentials are not forwarded to another origin", async () => {
    const MARKS = ["APIKEYMARK2290", "COOKIEMARK5521", "PROXYAUTHMARK8812"]
    await httpExecutor
      .request(
        opts("/api/releases", {
          Accept: "application/json",
          "X-Api-Key": MARKS[0],
          Cookie: `session=${MARKS[1]}`,
          "Proxy-Authorization": `Basic ${MARKS[2]}`,
        }),
        new CancellationToken()
      )
      .catch(() => null)

    for (const m of MARKS) {
      expect(localHeadersContain(b.seen, m), m).toEqual([])
    }
  })

  test("API request: a PRIVATE-TOKEN header is not forwarded to another origin", async () => {
    const MARK = "PRIVTOKENMARK6603"
    await httpExecutor.request(opts("/api/v4/projects/7/releases", { "PRIVATE-TOKEN": MARK }), new CancellationToken()).catch(() => null)
    expect(localHeadersContain(b.seen, MARK)).toEqual([])
  })

  test("download: a capitalised Authorization header is not forwarded to another origin", async () => {
    const MARK = "DLAUTHMARK3317"
    await httpExecutor
      .downloadToBuffer(new URL("/assets/app.zip", a.origin), { headers: { Authorization: `token ${MARK}` }, cancellationToken: new CancellationToken() })
      .catch(() => null)
    expect(localHeadersContain(b.seen, MARK)).toEqual([])
  })
})
