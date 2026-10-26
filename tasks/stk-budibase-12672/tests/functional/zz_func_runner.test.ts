/**
 * Hidden functional suite — the query thread runner's URL handling must keep
 * working for legitimate queries: run-time expanded paths that stay on the
 * datasource's origin, template datasources whose base address is rewritten by
 * the runner, and datasources with no base address whose saved path names the
 * host directly.
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
    path: "data",
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

describe("legitimate queries keep working through the runner", () => {
  it("TestFunc_ParameterizedPathSameOrigin", async () => {
    const evt = event({ parameters: { target: "data" } })
    evt.datasource.config.url = OWN
    evt.fields.path = "{{target}}"
    responders = [jsonOk({ rows: [] })]

    await run(evt)

    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://api.example.com/data")
    expect(calls[0].headers["x-static-secret"]).toBe(HDR_MARKER)
    expect(calls[0].headers["authorization"]).toBe(`Bearer ${TOKEN_MARKER}`)
  })

  it("TestFunc_TemplateBaseRewrite", async () => {
    const evt = event({ parameters: {} })
    evt.datasource.config.url = OWN
    evt.datasource.restTemplateId = "gitlab"
    evt.fields.path = "https://old.example.net/api/v1/users"
    responders = [jsonOk({ rows: [] })]

    await run(evt)

    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://api.example.com/api/v1/users")
    expect(calls[0].headers["x-static-secret"]).toBe(HDR_MARKER)
  })

  it("TestFunc_NoBaseAddressBareHostThroughRunner", async () => {
    const evt = event({ parameters: {} })
    evt.fields.path = "www.example.com/data"
    responders = [jsonOk({ rows: [] })]

    await run(evt)

    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe("http://www.example.com/data")
    expect(calls[0].headers["authorization"]).toBe(`Bearer ${TOKEN_MARKER}`)
  })
})
