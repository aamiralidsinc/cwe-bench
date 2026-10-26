/**
 * Hidden security suite — stored REST datasource credentials must never be
 * delivered to an origin other than the one the datasource is configured for.
 *
 * Every test drives the product's REST datasource integration (the component the
 * query runner instantiates and calls for every query route) and records the
 * outbound requests it makes.  The assertion is behavioural: no stored credential
 * value may appear in any request whose origin is not the datasource's own.
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

const leakedOffOrigin = (ownOrigin: string): boolean => {
  const foreign = calls.filter(call => {
    try {
      return new URL(call.url).origin !== ownOrigin
    } catch {
      return true
    }
  })
  const text = JSON.stringify(foreign)
  return (
    text.includes(HDR_MARKER) ||
    text.includes(TOKEN_MARKER) ||
    text.includes(APIKEY_MARKER) ||
    text.toLowerCase().includes("x-static-secret") ||
    text.toLowerCase().includes("x-custom-key")
  )
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

describe("stored credentials stay on the datasource origin", () => {
  it("TestSec_AbsolutePathForeignHost", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk()]

    await ds
      .read(query({ path: "http://collector.example.net/data" }))
      .catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_AbsolutePathLookalikeHost", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk()]

    await ds
      .read(query({ path: "http://api.example.com.collector.example.net/data" }))
      .catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_AbsolutePathDifferentPort", async () => {
    const ds = datasource({ url: "http://api.example.com:8080" })
    responders = [jsonOk()]

    await ds
      .read(query({ path: "http://api.example.com:9090/data" }))
      .catch(() => undefined)

    expect(leakedOffOrigin("http://api.example.com:8080")).toBe(false)
  })

  it("TestSec_AbsolutePathDifferentScheme", async () => {
    const ds = datasource({ url: "http://api.example.com" })
    responders = [jsonOk()]

    await ds
      .read(query({ path: "https://api.example.com/data" }))
      .catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_SchemeLessBaseForeignHost", async () => {
    const ds = datasource({ url: "api.example.com" })
    responders = [jsonOk()]

    await ds
      .read(query({ path: "http://collector.example.net/data" }))
      .catch(() => undefined)

    expect(leakedOffOrigin("http://api.example.com")).toBe(false)
  })

  it("TestSec_WritePathForeignHost", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk()]

    await ds
      .create(
        query({
          path: "http://collector.example.net/data",
          bodyType: "json",
          requestBody: '{"probe":"write"}',
        })
      )
      .catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_ApiKeyHeaderPathForeignHost", async () => {
    const ds = datasource({ url: OWN })
    responders = [jsonOk()]

    await ds
      .read(
        query({
          path: "http://collector.example.net/data",
          authConfigId: "auth-apikey",
          authConfigType: "apiKey",
        })
      )
      .catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })
})

describe("stored credentials do not follow a redirect off the origin", () => {
  it("TestSec_RedirectForeignHost", async () => {
    const ds = datasource({ url: OWN })
    responders = [redirect(302, "http://collector.example.net/data"), jsonOk()]

    await ds.read(query()).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_RedirectForeignHostProtocolRelative", async () => {
    const ds = datasource({ url: OWN })
    responders = [redirect(302, "//collector.example.net/data"), jsonOk()]

    await ds.read(query()).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_RedirectForeignHostCustomApiKeyHeader", async () => {
    const ds = datasource({ url: OWN })
    responders = [redirect(307, "http://collector.example.net/data"), jsonOk()]

    await ds
      .read(query({ authConfigId: "auth-apikey", authConfigType: "apiKey" }))
      .catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_RedirectLookalikeHost", async () => {
    const ds = datasource({ url: OWN })
    responders = [
      redirect(308, "http://api.example.com.collector.example.net/data"),
      jsonOk(),
    ]

    await ds.read(query()).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })
})
