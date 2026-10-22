// The Gitea publisher keeps working: uploads complete with their credential, redirects on the
// same origin keep it, and configuration diagnostics stay useful.
import { createRequire } from "node:module"
import * as path from "node:path"
import { CancellationToken } from "builder-util-runtime"
import { GiteaPublisher } from "electron-publish/out/giteaPublisher"
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"
import { LocalServer, startServer } from "../support/harness"

const APP = process.env.EB_APP_ROOT ?? "/app"
const context = { cancellationToken: new CancellationToken(), progress: null }
const token = "gitea_VALIDTOKEN0123456789"

function publisher(url: string, extra: Record<string, unknown> = {}) {
  return new GiteaPublisher(context, { provider: "gitea", url, owner: "o", repo: "r", token, ...extra } as any, "1.0.1")
}

describe("artifact upload", () => {
  let a: LocalServer
  let b: LocalServer
  afterEach(async () => {
    await a?.close()
    await b?.close()
  })

  test("an upload without a redirect sends the credential and completes", async () => {
    a = await startServer(() => ({ status: 201, headers: { "content-type": "application/json" }, body: "{}" }))
    await publisher(a.origin).upload({ file: "/tmp/cwe-asset.bin", fileContent: Buffer.from("payload-one"), arch: null })
    expect(a.seen.length).toBe(1)
    expect(a.seen[0].headers["authorization"]).toBe(`token ${token}`)
    expect(a.seen[0].path).toContain("name=cwe-asset.bin")
  })

  test("an upload redirected on the same origin keeps the credential and completes", async () => {
    a = await startServer(req => {
      if (req.url?.startsWith("/api/")) return { status: 307, headers: { location: "/storage/asset" } }
      return { status: 201, headers: { "content-type": "application/json" }, body: "{}" }
    })
    await publisher(a.origin).upload({ file: "/tmp/cwe-asset.bin", fileContent: Buffer.from("payload-two"), arch: null })
    const storage = a.seen.filter(r => r.path.startsWith("/storage/"))
    expect(storage.length).toBe(1)
    expect(storage[0].headers["authorization"]).toBe(`token ${token}`)
  })

  test("an upload redirected to another origin completes", async () => {
    b = await startServer(() => ({ status: 201, headers: { "content-type": "application/json" }, body: "{}" }))
    a = await startServer(() => ({ status: 307, headers: { location: `${b.origin}/storage/asset` } }))
    await publisher(a.origin).upload({ file: "/tmp/cwe-asset.bin", fileContent: Buffer.from("payload-three"), arch: null })
    expect(b.seen.length).toBe(1)
    expect(b.seen[0].headers["content-type"]).toBe("application/octet-stream")
    expect(b.seen[0].body).toBe("payload-three")
  })
})

describe("configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  test("a missing token is refused, naming the variable", () => {
    vi.stubEnv("GITEA_TOKEN", "")
    expect(() => new GiteaPublisher(context, { provider: "gitea", url: "http://127.0.0.1:9", owner: "o", repo: "r" } as any, "1.0.1")).toThrow(/GITEA_TOKEN/)
  })

  test("a valid token is accepted", () => {
    expect(() => publisher("http://127.0.0.1:9")).not.toThrow()
  })

  test("debug output still shows the instance it publishes to", () => {
    const output: Array<string> = []
    const debugModule = createRequire(path.join(APP, "packages/builder-util/package.json"))("debug")
    debugModule.enable("electron-builder")
    const capture = (chunk: any) => {
      output.push(String(chunk))
      return true
    }
    vi.spyOn(process.stderr, "write").mockImplementation(capture as any)
    vi.spyOn(process.stdout, "write").mockImplementation(capture as any)
    try {
      publisher("http://gitea.example.test")
    } finally {
      vi.restoreAllMocks()
      debugModule.disable()
    }
    expect(output.join("")).toContain("gitea.example.test")
  })
})
