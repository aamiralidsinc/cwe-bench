/**
 * Hidden security suite — a query path that is expanded at run time must not
 * carry the datasource's stored credentials to a different origin than the one
 * the query's own definition and the datasource's configuration imply.
 *
 * The tests drive the query thread runner (the product's query execution entry)
 * with the real REST datasource integration, and record every outbound request.
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

jest.mock("../../sdk/utils", () => {
  const actual = jest.requireActual("../../sdk/utils")
  return {
    ...actual,
    getEnvironmentVariables: jest.fn(async () => ({})),
  }
})

jest.mock("../../sdk", () => {
  const queries = jest.requireActual("../../sdk/workspace/queries/queries")
  return {
    __esModule: true,
    default: { queries: { enrichContext: queries.enrichContext } },
  }
})

jest.mock("@budibase/backend-core", () => {
  const actual = jest.requireActual("@budibase/backend-core")
  return {
    ...actual,
    context: {
      ...actual.context,
      doInWorkspaceContext: (_appId: string, fn: () => unknown) => fn(),
      doInEnvironmentContext: (_env: unknown, fn: () => unknown) => fn(),
    },
  }
})

jest.mock("../../integrations", () => ({ getIntegration: jest.fn() }))

jest.mock("../utils", () => {
  const actual = jest.requireActual("../utils")
  return {
    ...actual,
    default: {
      ...actual.default,
      threadSetup: jest.fn(),
      formatResponse: (response: unknown) => response,
    },
  }
})

import { Response } from "undici"
import * as undici from "undici"
import { getIntegration } from "../../integrations"
import { execute } from "../query"

const { RestIntegration } = jest.requireActual("../../integrations/rest")

jest.setTimeout(60000)

const HDR_MARKER = "DS_HEADER_MARKER_7Q4"
const TOKEN_MARKER = "DS_TOKEN_MARKER_7Q4"
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
    text.toLowerCase().includes("x-static-secret") ||
    text.toLowerCase().includes("authorization")
  )
}

const authConfigs = () => [
  {
    _id: "auth-bearer",
    name: "Bearer",
    type: "bearer",
    config: { token: TOKEN_MARKER },
  },
]

const event = (overrides: Record<string, unknown> = {}): any => ({
  appId: "app_test",
  datasource: {
    _id: "ds_1",
    type: "datasource",
    name: "test datasource",
    source: "REST",
    isSQL: false,
    config: {
      defaultHeaders: { "X-Static-Secret": HDR_MARKER },
      authConfigs: authConfigs(),
    },
  },
  queryVerb: "read",
  queryId: "q_1",
  fields: {
    path: "{{target}}",
    queryString: "",
    headers: {},
    bodyType: "none",
    authConfigId: "auth-bearer",
    authConfigType: "bearer",
  },
  parameters: {},
  transformer: null,
  schema: {},
  nullDefaultSupport: false,
  ...overrides,
})

const run = (evt: any): Promise<void> =>
  new Promise((resolve, reject) => {
    execute(evt, (err: unknown) => {
      if (err) {
        // eslint-disable-next-line no-console
        console.error("HIDDEN_RUNNER_ERROR", err)
        reject(err)
      } else {
        resolve()
      }
    })
  })

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
  ;(getIntegration as jest.Mock).mockImplementation(async () => RestIntegration)
})

describe("run-time expanded paths stay on the datasource origin", () => {
  it("TestSec_ParameterPathForeignHostWithoutBase", async () => {
    responders = [jsonOk()]

    await run(
      event({ parameters: { target: "http://collector.example.net/data" } })
    ).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_ParameterPathForeignHostWithBase", async () => {
    const evt = event({
      parameters: { target: "http://collector.example.net/data" },
    })
    evt.datasource.config.url = OWN
    responders = [jsonOk()]

    await run(evt).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_ParameterPathSchemeChange", async () => {
    const evt = event({
      parameters: { target: "https://api.example.com/data" },
    })
    evt.datasource.config.url = OWN
    responders = [jsonOk()]

    await run(evt).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })

  it("TestSec_ParameterPathPortChange", async () => {
    const evt = event({
      parameters: { target: "http://api.example.com:9090/data" },
    })
    evt.datasource.config.url = "http://api.example.com:8080"
    responders = [jsonOk()]

    await run(evt).catch(() => undefined)

    expect(leakedOffOrigin("http://api.example.com:8080")).toBe(false)
  })

  it("TestSec_ParameterPathLookalikeHost", async () => {
    const evt = event({
      parameters: { target: "http://api.example.com.collector.example.net/x" },
    })
    evt.datasource.config.url = OWN
    responders = [jsonOk()]

    await run(evt).catch(() => undefined)

    expect(leakedOffOrigin(OWN)).toBe(false)
  })
})
