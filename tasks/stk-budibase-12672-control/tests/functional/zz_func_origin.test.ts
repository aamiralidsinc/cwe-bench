/**
 * Hidden functional suite — legitimate REST datasource requests must keep
 * working exactly as today: relative and same-origin absolute paths, stored
 * header/auth credentials on the datasource's own origin, headers with custom
 * names, datasources with no base address, and same-origin redirects.
 */
jest.mock("undici", () => {
  const actual = jest.requireActual("undici")
  return { ...actual, fetch: jest.fn() }
})

jest.mock("@budibase/backend-core/src/blacklist", () => ({
  resolveAddress: jest.fn(async () => ["203.0.113.10"]),
  isBlacklisted: jest.fn(async () => false),
  refreshBlacklist: jest.fn(async () => {}),
}))

jest.mock("../../sdk/workspace/oauth2", () => {
  const actual = jest.requireActual("../../sdk/workspace/oauth2")
  return {
    ...actual,
    getToken: jest.fn(async () => "Bearer OAUTH_TOKEN_MARKER"),
    getTokenFromConfig: jest.fn(async () => "Bearer OAUTH_TOKEN_MARKER"),
    cleanStoredTokensForAuthConfig: jest.fn(async () => {}),
  }
})

import "../../sdk"
import { Response } from "undici"
import * as undici from "undici"
import { RestIntegration } from "../rest"

jest.setTimeout(60000)

const HDR_MARKER = "DS_HEADER_MARKER_7Q4"
const TOKEN_MARKER = "DS_TOKEN_MARKER_7Q4"
const APIKEY_MARKER = "DS_APIKEY_MARKER_7Q4"
const OWN = "http://api.example.com"

type Recorded = {
  url: string
  method?: string
  headers: Record<string, string>
  body: string
}
type Responder = (url: string) => Response

let calls: Recorded[] = []
let responders: Responder[] = []

const fetchMock = undici.fetch as unknown as jest.Mock

const jsonOk =
  (body: unknown = { ok: true }): Responder =>
  () =>
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    })

const redirect =
  (status: number, location: string): Responder =>
  () =>
    new Response(null, { status, headers: { location } })

const authConfigs = () => [
  {
    _id: "auth-bearer",
    name: "Bearer",
    type: "bearer",
    config: { token: TOKEN_MARKER },
  },
  {
    _id: "auth-apikey",
    name: "Api key",
    type: "apiKey",
    config: { key: "X-Custom-Key", value: APIKEY_MARKER, location: "header" },
  },
  {
    _id: "auth-basic",
    name: "Basic",
    type: "basic",
    config: { username: "the-user", password: "the-pass" },
  },
]

const datasource = (config: Record<string, unknown> = {}) =>
  new RestIntegration({
    defaultHeaders: { "X-Static-Secret": HDR_MARKER },
    authConfigs: authConfigs(),
    ...config,
  } as any)

const recordRequest = (url: unknown, init: any): void => {
  const headers: Record<string, string> = {}
  const raw = init?.headers || {}
  if (raw && typeof raw.forEach === "function" && !Array.isArray(raw)) {
    raw.forEach((value: unknown, key: string) => {
      headers[String(key).toLowerCase()] = String(value)
    })
  } else {
    for (const [key, value] of Object.entries(raw)) {
      headers[String(key).toLowerCase()] = String(value)
    }
  }
  const body =
    typeof init?.body === "string"
      ? init.body
      : init?.body
        ? String(init.body)
        : ""
  calls.push({ url: String(url), method: init?.method, headers, body })
}

const query = (extra: Record<string, unknown> = {}) =>
  ({
    path: "data",
    queryString: "",
    headers: {},
    bodyType: "none",
    authConfigId: "auth-bearer",
    authConfigType: "bearer",
    ...extra,
  }) as any

beforeEach(() => {
  calls = []
  responders = []
  fetchMock.mockReset()
  fetchMock.mockImplementation(async (url: unknown, init: any) => {
    recordRequest(url, init)
    const next = responders.shift()
    if (!next) {
      throw new Error(`unexpected outbound request to ${String(url)}`)
    }
    return next(String(url))
  })
})

describe("legitimate REST requests keep working", () => {
  it("TestFunc_RelativePathSameOrigin", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk({ rows: [] })]

    const response = await ds.read(query({ path: "data" }))

    expect(response.data).toEqual({ rows: [] })
    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://api.example.com/data")
    expect(calls[0].headers["x-static-secret"]).toBe(HDR_MARKER)
    expect(calls[0].headers["authorization"]).toBe(`Bearer ${TOKEN_MARKER}`)
  })

  it("TestFunc_AbsolutePathSameOrigin", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk({ ok: true })]

    await ds.read(query({ path: "http://api.example.com/data" }))

    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://api.example.com/data")
    expect(calls[0].headers["x-static-secret"]).toBe(HDR_MARKER)
  })

  it("TestFunc_CustomHeaderNameSameOrigin", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk({ ok: true })]

    await ds.read(
      query({ authConfigId: "auth-apikey", authConfigType: "apiKey" })
    )

    expect(calls).toHaveLength(1)
    expect(calls[0].headers["x-custom-key"]).toBe(APIKEY_MARKER)
    expect(calls[0].headers["x-static-secret"]).toBe(HDR_MARKER)
  })

  it("TestFunc_NoBaseAddressBareHostWithCredentials", async () => {
    const ds = datasource({})
    responders = [jsonOk({ ok: true })]

    await ds.read(
      query({
        path: "www.example.com/data",
        authConfigId: "auth-basic",
        authConfigType: "basic",
      })
    )

    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://www.example.com/data")
    const expected = Buffer.from("the-user:the-pass").toString("base64")
    expect(calls[0].headers["authorization"]).toBe(`Basic ${expected}`)
  })

  it("TestFunc_SameOriginRedirectKeepsCredentials", async () => {
    const ds = datasource({ url: OWN })
    responders = [redirect(302, "/final"), jsonOk({ ok: true })]

    await ds.read(query({ path: "data" }))

    expect(calls).toHaveLength(2)
    expect(calls[1].url).toBe("http://api.example.com/final")
    expect(calls[1].headers["x-static-secret"]).toBe(HDR_MARKER)
    expect(calls[1].headers["authorization"]).toBe(`Bearer ${TOKEN_MARKER}`)
  })
})
