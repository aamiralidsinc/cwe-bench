// Configured secrets must not appear in clear text in error messages or debug output.
import { createRequire } from "node:module"
import * as path from "node:path"
import { CancellationToken } from "builder-util-runtime"
import { httpExecutor } from "builder-util"
import { GitHubPublisher } from "electron-publish/out/gitHubPublisher"
import { GitlabPublisher } from "electron-publish/out/gitlabPublisher"
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"
import { LocalServer, startServer } from "../support/harness"

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

describe("publish token configuration errors", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  test("GitHub: a GH_TOKEN with an invalid character is not echoed in the error", () => {
    vi.stubEnv("GITHUB_RELEASE_TOKEN", "")
    vi.stubEnv("GITHUB_TOKEN", "")
    vi.stubEnv("GH_TOKEN", "ghp_GHTOKENSECRET4471:x")
    const text = errorText(() => new GitHubPublisher(context, { provider: "github", owner: "o", repo: "r" }, "1.0.1"))
    expect(text).not.toContain("GHTOKENSECRET4471")
  })

  test("GitLab: a GITLAB_TOKEN with an invalid character is not echoed in the error", () => {
    vi.stubEnv("GITLAB_TOKEN", "glpat-GLTOKENSECRET8820 x")
    const text = errorText(() => new GitlabPublisher(context, { provider: "gitlab", projectId: 42 } as any, "1.0.1"))
    expect(text).not.toContain("GLTOKENSECRET8820")
  })
})

describe("debug output (DEBUG=electron-builder)", () => {
  let server: LocalServer
  let output: Array<string>
  let debugModule: any
  beforeEach(async () => {
    server = await startServer(() => ({ status: 200, headers: { "content-type": "application/json" }, body: "{}" }))
    output = []
    debugModule = createRequire(path.join(APP, "packages/builder-util-runtime/package.json"))("debug")
    debugModule.enable("electron-builder")
    const capture = (chunk: any) => {
      output.push(String(chunk))
      return true
    }
    vi.spyOn(process.stderr, "write").mockImplementation(capture as any)
    vi.spyOn(process.stdout, "write").mockImplementation(capture as any)
  })
  afterEach(async () => {
    vi.restoreAllMocks()
    debugModule.disable()
    await server.close()
  })

  test("a JSON request body's password, API key and client secret are not logged in clear", async () => {
    const SECRETS = ["BODYPASSWORD5512", "BODYAPIKEY7734", "BODYCLIENTSECRET1290"]
    const u = new URL("/api/releases", server.origin)
    await httpExecutor
      .request({ protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname }, new CancellationToken(), {
        tag_name: "v1.0.1",
        password: SECRETS[0],
        apiKey: SECRETS[1],
        clientSecret: SECRETS[2],
      })
      .catch(() => null)
    const text = output.join("")
    for (const s of SECRETS) {
      expect(text, s).not.toContain(s)
    }
  })
})
