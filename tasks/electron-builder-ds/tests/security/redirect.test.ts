// Credentials attached to a request must not reach another origin when a server redirects.
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
  LocalServer,
  localHeadersContain,
  NEW_VERSION,
  pathOf,
  serveBytes,
  startServer,
} from "../support/harness"

const FEED = "https://updates.example.test/feed/"
const CDN = "https://downloads.cdn-elsewhere.test"

describe("publishing HTTP client (Node)", () => {
  let a: LocalServer
  let b: LocalServer

  beforeEach(async () => {
    b = await startServer(() => ({ status: 200, headers: { "content-type": "application/json" }, body: "{}" }))
  })
  afterEach(async () => {
    await a?.close()
    await b?.close()
  })

  const opts = (path: string, headers: Record<string, string>) => {
    const u = new URL(path, a.origin)
    return { protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname, headers }
  }

  test("standard and application credential headers are not forwarded to another origin", async () => {
    a = await startServer(req => ({ status: 307, headers: { location: `${b.origin}/moved${req.url}` } }))
    const MARKS = ["AUTHMARK2290", "PRIVTOKENMARK5521", "APIKEYMARK8812", "COOKIEMARK3391", "PROXYAUTHMARK7714", "AMZTOKENMARK6684"]
    await httpExecutor
      .request(
        opts("/api/releases", {
          Accept: "application/json",
          Authorization: `Bearer ${MARKS[0]}`,
          "PRIVATE-TOKEN": MARKS[1],
          "X-Api-Key": MARKS[2],
          Cookie: `session=${MARKS[3]}`,
          "Proxy-Authorization": `Basic ${MARKS[4]}`,
          "X-Amz-Security-Token": MARKS[5],
        }),
        new CancellationToken()
      )
      .catch(() => null)

    for (const m of MARKS) {
      expect(localHeadersContain(b.seen, m), m).toEqual([])
    }
  })

  test("case and separator variants of credential header names are not forwarded to another origin", async () => {
    a = await startServer(req => ({ status: 302, headers: { location: `${b.origin}/moved${req.url}` } }))
    const MARKS = ["UPPERAUTHMARK6603", "UNDERSCOREPRIVMARK1172", "UNDERSCOREAPIKEYMARK4458", "AUTHTOKENMARK9002", "GITLABTOKENMARK3157", "ACCESSTOKENMARK6630"]
    await httpExecutor
      .request(
        opts("/api/v4/projects/7/releases", {
          AUTHORIZATION: `Bearer ${MARKS[0]}`,
          PRIVATE_TOKEN: MARKS[1],
          X_API_KEY: MARKS[2],
          "X-Auth-Token": MARKS[3],
          "X-Gitlab-Token": MARKS[4],
          "x-access-token": MARKS[5],
        }),
        new CancellationToken()
      )
      .catch(() => null)

    for (const m of MARKS) {
      expect(localHeadersContain(b.seen, m), m).toEqual([])
    }
  })

  test("a redirect to another port on the same host does not receive credentials", async () => {
    a = await startServer(req => ({ status: 308, headers: { location: `${b.origin}/moved${req.url}` } }))
    const MARK = "PORTREDIRECTMARK7089"
    await httpExecutor.request(opts("/api/releases", { "X-Api-Key": MARK }), new CancellationToken()).catch(() => null)
    expect(localHeadersContain(b.seen, MARK)).toEqual([])
  })

  test("basic authentication credentials are not forwarded to another origin", async () => {
    a = await startServer(req => ({ status: 302, headers: { location: `${b.origin}/moved${req.url}` } }))
    const SECRET = "BASICAUTHMARK2207"
    // Node turns `auth` into an Authorization: Basic header on the wire.
    const headerValue = `Basic ${Buffer.from(`publisher:${SECRET}`).toString("base64")}`
    const u = new URL("/api/releases", a.origin)
    await httpExecutor
      .request({ protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname, auth: `publisher:${SECRET}` }, new CancellationToken())
      .catch(() => null)

    expect(localHeadersContain(b.seen, headerValue)).toEqual([])
  })

  test("a download redirected to another origin does not receive the credential", async () => {
    a = await startServer(req => ({ status: 302, headers: { location: `${b.origin}/blob${req.url}` } }))
    const MARK = "DLAUTHMARK3317"
    await httpExecutor
      .downloadToBuffer(new URL("/assets/app.zip", a.origin), { headers: { Authorization: `token ${MARK}` }, cancellationToken: new CancellationToken() })
      .catch(() => null)
    expect(localHeadersContain(b.seen, MARK)).toEqual([])
  })
})

describe("app updater (Electron net)", () => {
  beforeEach(() => resetNet())

  test("a full update download redirected to another origin does not receive the credential", async () => {
    const MARK = "UPDATERFULLDLMARK9124"
    const file = bytes("updater-full-cross", 4096)
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
})
