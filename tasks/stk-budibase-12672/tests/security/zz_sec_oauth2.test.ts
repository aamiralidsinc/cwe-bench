/**
 * Hidden security suite — a stored OAuth2 client credential is a datasource
 * credential: it must not be re-sent to an origin other than the token endpoint
 * the credential is configured for, whatever part of the request carries it.
 *
 * The test drives the product's stored-OAuth2-config token acquisition helper and
 * records every outbound request.
 */
jest.mock("node-fetch", () => {
  const actual = jest.requireActual("node-fetch")
  const fn = jest.fn()
  return Object.assign(fn, {
    Headers: actual.Headers,
    Response: actual.Response,
  })
})

jest.mock("@budibase/backend-core/src/blacklist", () => ({
  resolveAddress: jest.fn(async () => ["203.0.113.10"]),
  isBlacklisted: jest.fn(async () => false),
  refreshBlacklist: jest.fn(async () => {}),
}))

jest.mock("../../../utils", () => ({
  processEnvironmentVariable: jest.fn(async (value: unknown) => value),
  getEnvironmentVariables: jest.fn(async () => ({})),
}))

jest.mock("@budibase/backend-core", () => {
  const actual = jest.requireActual("@budibase/backend-core")
  return {
    ...actual,
    cache: {
      ...actual.cache,
      withCacheWithDynamicTTL: (_key: string, fn: () => unknown) => fn(),
    },
  }
})

import nodeFetch from "node-fetch"
import { getTokenFromConfig } from "../utils"

jest.setTimeout(60000)

const SECRET = "OAUTH_CLIENT_SECRET_MARKER_5Z"
const IDP = "http://idp.example.com"
const TOKEN_PATH = "/token"

type Recorded = {
  url: string
  method?: string
  headers: Record<string, string>
  body: string
}
type Responder = (url: string) => any

let calls: Recorded[] = []
let responders: Responder[] = []

const fetchMock = nodeFetch as unknown as jest.Mock
const { Response } = jest.requireActual("node-fetch")

const jsonOk =
  (body: unknown): Responder =>
  () =>
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    })

const redirect =
  (status: number, location: string): Responder =>
  () =>
    new Response(null, { status, headers: { location } })

const recordRequest = (url: unknown, init: any): void => {
  const headers: Record<string, string> = {}
  const raw = init?.headers || {}
  for (const [key, value] of Object.entries(raw)) {
    headers[String(key).toLowerCase()] = String(value)
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
  return JSON.stringify(foreign).includes(SECRET)
}

const config = (overrides: Record<string, unknown> = {}) => ({
  url: `${IDP}${TOKEN_PATH}`,
  clientId: "client-id-1",
  clientSecret: SECRET,
  method: "BODY",
  grantType: "client_credentials",
  ...overrides,
})

const tokenBody = {
  token_type: "Bearer",
  access_token: "access-token-value",
  expires_in: 3600,
}

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

describe("stored OAuth2 client credentials stay on the token endpoint origin", () => {
  it("TestSec_OAuth2TokenRedirectForeignHostBody", async () => {
    responders = [
      redirect(307, "http://collector.example.net/token"),
      jsonOk(tokenBody),
    ]

    await getTokenFromConfig("cache-key-1", config() as any).catch(
      () => undefined
    )

    expect(leakedOffOrigin(IDP)).toBe(false)
  })

  it("TestSec_OAuth2TokenRedirectForeignHostPreservingMethod", async () => {
    responders = [
      redirect(308, "http://collector.example.net/token"),
      jsonOk(tokenBody),
    ]

    await getTokenFromConfig("cache-key-2", config() as any).catch(
      () => undefined
    )

    expect(leakedOffOrigin(IDP)).toBe(false)
  })
})
