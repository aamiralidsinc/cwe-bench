// Block-based (differential) update download: credentials must not reach another origin when the
// update file redirects. The auth header is set with the updater's own shortcut.
import { beforeEach, expect, test } from "vitest"
import { FakeResponse, resetNet, SeenRequest, serve } from "../support/fakeElectron"
import {
  anyHeaderContains,
  blockMap,
  channelYaml,
  createUpdater,
  headersSeenOutside,
  INSTALLER,
  installerPair,
  NEW_VERSION,
  OLD_VERSION,
  pathOf,
  serveBytes,
} from "../support/harness"

const FEED = "https://updates.example.test/feed/"
const CDN = "https://downloads.cdn-elsewhere.test"

beforeEach(() => resetNet())

test("differential download: the auth token is not sent to the host the update file redirects to", async () => {
  const MARK = "DIFFAUTHMARK9046"
  const { oldFile, newFile } = installerPair()
  serve(FEED, req => {
    const p = pathOf(req)
    if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(newFile) }
    if (p.endsWith(`/${INSTALLER(NEW_VERSION)}.blockmap`)) return { status: 200, body: blockMap(newFile) }
    if (p.endsWith(`/${INSTALLER(OLD_VERSION)}.blockmap`)) return { status: 200, body: blockMap(oldFile) }
    if (p.endsWith(`/${INSTALLER(NEW_VERSION)}`)) return { status: 302, headers: { location: `${CDN}/blobs/${INSTALLER(NEW_VERSION)}` } }
    return { status: 404 }
  })
  serve(CDN, req => serveBytes(req, newFile))

  const updater = createUpdater({ provider: "generic", url: FEED, useMultipleRangeRequest: false }, oldFile)
  updater.addAuthHeader(`Bearer ${MARK}`)
  await updater.checkForUpdates()
  await updater.downloadUpdate().catch(() => null)

  expect(anyHeaderContains(headersSeenOutside(FEED), MARK)).toEqual([])
})

/** Serves `buf` for a multi-range `Range: bytes=a-b, c-d` request as multipart/byteranges. */
function serveByteRanges(req: SeenRequest, buf: Buffer): FakeResponse {
  const range = req.headers["range"]
  if (range == null || !range.includes(",")) {
    return serveBytes(req, buf)
  }
  const boundary = "cwe-bench-byteranges"
  const parts: Array<Buffer> = []
  for (const spec of range.replace(/^bytes=/, "").split(",")) {
    const m = /^(\d+)-(\d+)$/.exec(spec.trim())
    if (m == null) {
      return { status: 416 }
    }
    const start = Number(m[1])
    const end = Number(m[2])
    parts.push(Buffer.from(`--${boundary}\r\nContent-Type: application/octet-stream\r\nContent-Range: bytes ${start}-${end}/${buf.length}\r\n\r\n`))
    parts.push(buf.subarray(start, end + 1))
    parts.push(Buffer.from("\r\n"))
  }
  parts.push(Buffer.from(`--${boundary}--\r\n`))
  return { status: 206, headers: { "content-type": `multipart/byteranges; boundary=${boundary}`, "accept-ranges": "bytes" }, body: Buffer.concat(parts) }
}

test("differential download with the default multi-range requests: an application credential header is not sent to the host the update file redirects to", async () => {
  const MARK = "MULTIRANGEKEYMARK5512"
  const { oldFile, newFile } = installerPair()
  serve(FEED, req => {
    const p = pathOf(req)
    if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(newFile) }
    if (p.endsWith(`/${INSTALLER(NEW_VERSION)}.blockmap`)) return { status: 200, body: blockMap(newFile) }
    if (p.endsWith(`/${INSTALLER(OLD_VERSION)}.blockmap`)) return { status: 200, body: blockMap(oldFile) }
    if (p.endsWith(`/${INSTALLER(NEW_VERSION)}`)) return { status: 302, headers: { location: `${CDN}/blobs/${INSTALLER(NEW_VERSION)}` } }
    return { status: 404 }
  })
  serve(CDN, req => serveByteRanges(req, newFile))

  const updater = createUpdater({ provider: "generic", url: FEED }, oldFile)
  updater.requestHeaders = { "X-Api-Key": MARK }
  await updater.checkForUpdates()
  await updater.downloadUpdate().catch(() => null)

  expect(anyHeaderContains(headersSeenOutside(FEED), MARK)).toEqual([])
})
