/**
 * Hidden functional suite — acquiring a stored OAuth2 token must keep working:
 * a normal token response, a same-origin redirect on the token endpoint, and
 * the header-credentials method.
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

const config = (overrides: Record<string, unknown> = {}) => ({
  url: `${IDP}/token`,
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

describe("OAuth2 token acquisition keeps working", () => {
  it("TestFunc_OAuth2TokenNormal", async () => {
    responders = [jsonOk(tokenBody)]

    const token = await getTokenFromConfig("cache-key-f1", config() as any)

    expect(token).toBe("Bearer access-token-value")
    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://idp.example.com/token")
    expect(calls[0].body).toContain("grant_type=client_credentials")
  })

  it("TestFunc_OAuth2TokenSameOriginRedirect", async () => {
    responders = [redirect(307, "/token-final"), jsonOk(tokenBody)]

    const token = await getTokenFromConfig("cache-key-f2", config() as any)

    expect(token).toBe("Bearer access-token-value")
    expect(calls).toHaveLength(2)
    expect(calls[1].url).toBe("http://idp.example.com/token-final")
  })

  it("TestFunc_OAuth2TokenHeaderCredentials", async () => {
    responders = [jsonOk(tokenBody)]

    const token = await getTokenFromConfig(
      "cache-key-f3",
      config({ method: "HEADER" }) as any
    )

    expect(token).toBe("Bearer access-token-value")
    expect(calls).toHaveLength(1)
    expect(calls[0].headers["authorization"]).toMatch(/^Basic /)
    expect(calls[0].body).not.toContain(SECRET)
  })
})
