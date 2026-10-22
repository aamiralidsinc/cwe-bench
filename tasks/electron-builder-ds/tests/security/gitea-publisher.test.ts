// The Gitea publisher must not hand its access token to another origin when an upload is
// redirected, must not echo a malformed token, and must not print it in debug output.
import { createRequire } from "node:module"
import * as path from "node:path"
import { CancellationToken } from "builder-util-runtime"
import { GiteaPublisher } from "electron-publish/out/giteaPublisher"
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"
import { LocalServer, localHeadersContain, startServer } from "../support/harness"

const APP = process.env.EB_APP_ROOT ?? "/app"
const context = { cancellationToken: new CancellationToken(), progress: null }

function errorText(fn: () => unknown): string {
  try {
    fn()
  } catch (e: any) {
    return `${e?.message ?? ""}\n${e?.stack ?? ""}\n${String(e)}`
  }
  return ""
}

describe("artifact upload redirect", () => {
  let a: LocalServer
  let b: LocalServer
  afterEach(async () => {
    await a?.close()
    await b?.close()
  })

  test("the access token is not sent to the storage origin an upload is redirected to", async () => {
    const MARK = "GITEAUPLOADTOKENMARK5520"
    b = await startServer(() => ({ status: 201, headers: { "content-type": "application/json" }, body: "{}" }))
    a = await startServer(() => ({ status: 307, headers: { location: `${b.origin}/objects/asset?sig=1` } }))

    const publisher = new GiteaPublisher(context, { provider: "gitea", url: a.origin, owner: "o", repo: "r", token: `gitea_${MARK}` }, "1.0.1")
    await publisher.upload({ file: "/tmp/cwe-gitea-asset.bin", fileContent: Buffer.from("artifact-payload"), arch: null }).catch(() => null)

    expect(localHeadersContain(b.seen, MARK)).toEqual([])
  })
})

describe("publisher token configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  test("a malformed GITEA_TOKEN is not echoed in the configuration error", () => {
    vi.stubEnv("GITEA_TOKEN", "gitea_GITEASECRET9981:x")
    const text = errorText(() => new GiteaPublisher(context, { provider: "gitea", url: "http://127.0.0.1:9", owner: "o", repo: "r" }, "1.0.1"))
    expect(text).not.toContain("GITEASECRET9981")
  })
})

describe("debug output (DEBUG=electron-builder)", () => {
  let output: Array<string>
  let debugModule: any
  beforeEach(() => {
    output = []
    debugModule = createRequire(path.join(APP, "packages/builder-util/package.json"))("debug")
    debugModule.enable("electron-builder")
    const capture = (chunk: any) => {
      output.push(String(chunk))
      return true
    }
    vi.spyOn(process.stderr, "write").mockImplementation(capture as any)
    vi.spyOn(process.stdout, "write").mockImplementation(capture as any)
  })
  afterEach(() => {
    vi.restoreAllMocks()
    debugModule.disable()
  })

  test("the publisher configuration's access token is not logged in clear", () => {
    const MARK = "GITEADEBUGTOKENMARK3312"
    new GiteaPublisher(context, { provider: "gitea", url: "http://gitea.example.test", owner: "o", repo: "r", token: `gitea_${MARK}` }, "1.0.1")
    expect(output.join("")).not.toContain(MARK)
  })
})
