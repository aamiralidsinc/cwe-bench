// Configured secrets must not appear in clear text in request-body debug output or in an error
// message built from a JSON error response.
import { createRequire } from "node:module"
import * as path from "node:path"
import { CancellationToken } from "builder-util-runtime"
import { httpExecutor } from "builder-util"
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"
import { LocalServer, startServer } from "../support/harness"

const APP = process.env.EB_APP_ROOT ?? "/app"

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

  test("a JSON request body's application-specific credential fields are not logged in clear", async () => {
    const MARKS = ["BODYPRIVTOKEN1123", "BODYAPIKEY7734", "BODYCLIENTSECRET1290", "BODYPASSPHRASE4402", "BODYCREDENTIAL6651"]
    const u = new URL("/api/releases", server.origin)
    await httpExecutor
      .request({ protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname }, new CancellationToken(), {
        tag_name: "v1.0.1",
        private_token: MARKS[0],
        apiKey: MARKS[1],
        clientSecret: MARKS[2],
        passphrase: MARKS[3],
        credential: MARKS[4],
      })
      .catch(() => null)

    const text = output.join("")
    for (const m of MARKS) {
      expect(text, m).not.toContain(m)
    }
  })
})

describe("error messages", () => {
  let server: LocalServer
  afterEach(async () => {
    await server.close()
  })

  test("a JSON error response's credential fields are not put in the error text", async () => {
    const MARKS = ["ERRAPIKEY2291", "ERRCLIENTSECRET5518", "ERRPASSPHRASE9903"]
    server = await startServer(() => ({
      status: 400,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ message: "bad request", apiKey: MARKS[0], clientSecret: MARKS[1], passphrase: MARKS[2] }),
    }))
    const u = new URL("/api/releases", server.origin)
    let text = ""
    try {
      await httpExecutor.request({ protocol: u.protocol, hostname: u.hostname, port: u.port, path: u.pathname }, new CancellationToken())
    } catch (e: any) {
      text = `${e?.message ?? ""}\n${String(e)}`
    }
    for (const m of MARKS) {
      expect(text, m).not.toContain(m)
    }
  })
})
