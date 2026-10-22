// Redaction keeps the diagnostic value: invalid tokens are still refused with a message naming
// the variable, valid ones are accepted, non-secret output stays visible, and debug output still
// shows ordinary request fields.
import { createRequire } from "node:module"
import * as path from "node:path"
import { exec } from "builder-util"
import { CancellationToken } from "builder-util-runtime"
import { GitHubPublisher } from "electron-publish/out/gitHubPublisher"
import { GitlabPublisher } from "electron-publish/out/gitlabPublisher"
import { httpExecutor } from "builder-util"
import { afterEach, describe, expect, test, vi } from "vitest"
import { startServer } from "../support/harness"

const APP = process.env.EB_APP_ROOT ?? "/app"
const context = { cancellationToken: new CancellationToken(), progress: null }

describe("publish token configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  test("GitHub: an invalid GH_TOKEN is still refused, naming the variable", () => {
    vi.stubEnv("GITHUB_RELEASE_TOKEN", "")
    vi.stubEnv("GITHUB_TOKEN", "")
    vi.stubEnv("GH_TOKEN", "ghp_invalid token")
    expect(() => new GitHubPublisher(context, { provider: "github", owner: "o", repo: "r" }, "1.0.1")).toThrow(/GH_TOKEN/)
  })

  test("GitHub: a valid GH_TOKEN is accepted", () => {
    vi.stubEnv("GITHUB_RELEASE_TOKEN", "")
    vi.stubEnv("GH_TOKEN", "ghp_valid0123456789")
    expect(() => new GitHubPublisher(context, { provider: "github", owner: "o", repo: "r" }, "1.0.1")).not.toThrow()
  })

  test("GitLab: an invalid GITLAB_TOKEN is still refused, naming the variable", () => {
    vi.stubEnv("GITLAB_TOKEN", "glpat-invalid token")
    expect(() => new GitlabPublisher(context, { provider: "gitlab", projectId: 42 } as any, "1.0.1")).toThrow(/GITLAB_TOKEN/)
  })

  test("GitLab: a valid GITLAB_TOKEN is accepted", () => {
    vi.stubEnv("GITLAB_TOKEN", "glpat-valid0123456789")
    expect(() => new GitlabPublisher(context, { provider: "gitlab", projectId: 42 } as any, "1.0.1")).not.toThrow()
  })
})

test("a failed command keeps its non-secret output and exit code in the error", async () => {
  let text = ""
  try {
    await exec("bash", ["-c", "printf '%s' 'ordinary diagnostic text' >&2; exit 2"])
  } catch (e: any) {
    text = `${e?.message ?? ""}\n${String(e)}`
  }
  expect(text).toContain("ordinary diagnostic text")
  expect(text).toContain("Exit code: 2")
})

test("an HTTP error keeps the non-secret message from a JSON error response", async () => {
  const server = await startServer(() => ({
    status: 400,
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message: "ordinary error detail", apiKey: "redacted-api-key-value" }),
  }))
  let text = ""
  try {
    const u = new URL("/api/releases", server.origin)
    await httpExecutor.request({ protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname }, new CancellationToken())
  } catch (e: any) {
    text = `${e?.message ?? ""}\n${String(e)}`
  } finally {
    await server.close()
  }
  expect(text).toContain("ordinary error detail")
})

test("debug output still shows a JSON request body's ordinary fields", async () => {
  const server = await startServer(() => ({ status: 200, headers: { "content-type": "application/json" }, body: "{}" }))
  const output: Array<string> = []
  const debugModule = createRequire(path.join(APP, "packages/builder-util-runtime/package.json"))("debug")
  debugModule.enable("electron-builder")
  const capture = (chunk: any) => {
    output.push(String(chunk))
    return true
  }
  vi.spyOn(process.stderr, "write").mockImplementation(capture as any)
  vi.spyOn(process.stdout, "write").mockImplementation(capture as any)
  try {
    const u = new URL("/api/releases", server.origin)
    await httpExecutor.request({ protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname }, new CancellationToken(), {
      tag_name: "v1.0.1-visibletag",
      draft: true,
    })
  } finally {
    vi.restoreAllMocks()
    debugModule.disable()
    await server.close()
  }
  expect(output.join("")).toContain("v1.0.1-visibletag")
})
