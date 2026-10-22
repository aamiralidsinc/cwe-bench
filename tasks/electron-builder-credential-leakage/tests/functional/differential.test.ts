// Block-based (differential) update downloads keep working, including through redirects.
import { readFileSync } from "node:fs"
import { beforeEach, expect, test } from "vitest"
import { resetNet, seenRequests, serve } from "../support/fakeElectron"
import { blockMap, channelYaml, createUpdater, INSTALLER, installerPair, NEW_VERSION, OLD_VERSION, pathOf, serveBytes, sha512 } from "../support/harness"

const FEED = "https://updates.example.test/feed/"
const CDN = "https://downloads.cdn-elsewhere.test"

beforeEach(() => resetNet())

function serveFeed(newFile: Buffer, oldFile: Buffer, installer: (req: any) => any) {
  serve(FEED, req => {
    const p = pathOf(req)
    if (p.endsWith("/latest-linux.yml")) return { status: 200, body: channelYaml(newFile) }
    if (p.endsWith(`/${INSTALLER(NEW_VERSION)}.blockmap`)) return { status: 200, body: blockMap(newFile) }
    if (p.endsWith(`/${INSTALLER(OLD_VERSION)}.blockmap`)) return { status: 200, body: blockMap(oldFile) }
    return installer(req)
  })
}

test("differential download without redirects fetches only the changed blocks", async () => {
  const { oldFile, newFile } = installerPair()
  serveFeed(newFile, oldFile, req => (pathOf(req) === `/feed/${INSTALLER(NEW_VERSION)}` ? serveBytes(req, newFile) : { status: 404 }))

  const updater = createUpdater({ provider: "generic", url: FEED, useMultipleRangeRequest: false }, oldFile)
  updater.addAuthHeader("Bearer plain-token")
  await updater.checkForUpdates()
  const [downloaded] = await updater.downloadUpdate()
  expect(sha512(readFileSync(downloaded))).toBe(sha512(newFile))
  const installerRequests = seenRequests().filter(r => pathOf(r).endsWith(".exe"))
  expect(installerRequests.length).toBeGreaterThan(0)
  expect(installerRequests.every(r => r.headers["range"] != null)).toBe(true)
})

test("differential download through a redirect to another host completes with the right file", async () => {
  const { oldFile, newFile } = installerPair()
  serveFeed(newFile, oldFile, req =>
    pathOf(req) === `/feed/${INSTALLER(NEW_VERSION)}` ? { status: 302, headers: { location: `${CDN}/blobs/${INSTALLER(NEW_VERSION)}` } } : { status: 404 }
  )
  serve(CDN, req => serveBytes(req, newFile))

  const updater = createUpdater({ provider: "generic", url: FEED, useMultipleRangeRequest: false }, oldFile)
  updater.addAuthHeader("Bearer cross-token")
  await updater.checkForUpdates()
  const [downloaded] = await updater.downloadUpdate()
  expect(sha512(readFileSync(downloaded))).toBe(sha512(newFile))
})

test("differential download through a redirect on the same server keeps the auth header", async () => {
  const { oldFile, newFile } = installerPair()
  serveFeed(newFile, oldFile, req => {
    const p = pathOf(req)
    if (p === `/feed/${INSTALLER(NEW_VERSION)}`) return { status: 302, headers: { location: `/storage/${INSTALLER(NEW_VERSION)}` } }
    if (p === `/storage/${INSTALLER(NEW_VERSION)}`) {
      return req.headers["authorization"] === "Bearer same-token" ? serveBytes(req, newFile) : { status: 401, body: "auth required" }
    }
    return { status: 404 }
  })

  const updater = createUpdater({ provider: "generic", url: FEED, useMultipleRangeRequest: false }, oldFile)
  updater.addAuthHeader("Bearer same-token")
  await updater.checkForUpdates()
  const [downloaded] = await updater.downloadUpdate()
  expect(sha512(readFileSync(downloaded))).toBe(sha512(newFile))
  const storage = seenRequests().filter(r => pathOf(r) === `/storage/${INSTALLER(NEW_VERSION)}`)
  expect(storage.length).toBeGreaterThan(0)
  expect(storage.every(r => r.headers["authorization"] === "Bearer same-token")).toBe(true)
})
