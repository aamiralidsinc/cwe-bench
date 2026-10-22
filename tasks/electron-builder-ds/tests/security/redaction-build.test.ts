// Configured secrets must not appear in clear text in command output captured into an error, nor
// in the error raised when a publish token is malformed.
import { exec } from "builder-util"
import { CancellationToken } from "builder-util-runtime"
import { GitHubPublisher } from "electron-publish/out/gitHubPublisher"
import { GitlabPublisher } from "electron-publish/out/gitlabPublisher"
import { afterEach, describe, expect, test, vi } from "vitest"

const context = { cancellationToken: new CancellationToken(), progress: null }

async function errorText(fn: () => unknown): Promise<string> {
  try {
    await fn()
  } catch (e: any) {
    return `${e?.message ?? ""}\n${e?.stack ?? ""}\n${String(e)}`
  }
  return ""
}

describe("command error output", () => {
  test("a credential in a failed command's standard error is not shown in clear", async () => {
    const MARK = "STDERRAPIKEYMARK7710"
    const text = await errorText(() => exec("bash", ["-c", "printf '%s' \"$CWE_PROBE\" >&2; exit 3"], { env: { ...process.env, CWE_PROBE: `--apiKey ${MARK}` } }))
    expect(text).not.toContain(MARK)
  })

  test("a credential in a failed command's standard output is not shown in clear", async () => {
    const MARK = "STDOUTPRIVTOKENMARK4468"
    const text = await errorText(() => exec("bash", ["-c", "printf '%s' \"$CWE_PROBE\"; exit 3"], { env: { ...process.env, CWE_PROBE: `--privateToken ${MARK}` } }))
    expect(text).not.toContain(MARK)
  })
})

describe("publish token configuration errors", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  test("GitHub: a GH_TOKEN with an invalid character is not echoed in the error", async () => {
    vi.stubEnv("GITHUB_RELEASE_TOKEN", "")
    vi.stubEnv("GITHUB_TOKEN", "")
    vi.stubEnv("GH_TOKEN", "ghp_GHTOKENSECRET4471:x")
    const text = await errorText(() => new GitHubPublisher(context, { provider: "github", owner: "o", repo: "r" }, "1.0.1"))
    expect(text).not.toContain("GHTOKENSECRET4471")
  })

  test("GitLab: a GITLAB_TOKEN with an invalid character is not echoed in the error", async () => {
    vi.stubEnv("GITLAB_TOKEN", "glpat-GLTOKENSECRET8820 x")
    const text = await errorText(() => new GitlabPublisher(context, { provider: "gitlab", projectId: 42 } as any, "1.0.1"))
    expect(text).not.toContain("GLTOKENSECRET8820")
  })
})
