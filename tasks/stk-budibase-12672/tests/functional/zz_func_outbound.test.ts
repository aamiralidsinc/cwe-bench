/**
 * Hidden functional suite — the shared outbound fetch helper is used by far more
 * than the REST integration.  Its existing behaviour (follow a redirect to
 * another origin; preserve method and body on 307/308) must keep working for
 * those callers.
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

import nodeFetch from "node-fetch"
import { utils as coreUtils } from "@budibase/backend-core"

jest.setTimeout(60000)

const { Response: NodeResponse } = jest.requireActual("node-fetch")
const fetchMock = nodeFetch as unknown as jest.Mock

beforeEach(() => {
  fetchMock.mockReset()
})

describe("the shared outbound helper keeps its behaviour for other callers", () => {
  it("TestFunc_OutboundHelperFollowsCrossOriginRedirect", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new NodeResponse(null, {
          status: 302,
          headers: { location: "https://other.example.com/final" },
        })
      )
      .mockResolvedValueOnce(
        new NodeResponse("done", {
          status: 200,
          headers: { "content-type": "text/plain" },
        })
      )

    const response = await coreUtils.fetchWithBlacklist(
      "https://api.example.com/resource",
      { headers: { "X-Custom": "value" } }
    )

    expect(response.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(String(fetchMock.mock.calls[1][0])).toBe(
      "https://other.example.com/final"
    )
  })

  it("TestFunc_OutboundHelperPreservesMethodAndBodyOn307", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new NodeResponse(null, {
          status: 307,
          headers: { location: "https://other.example.com/final" },
        })
      )
      .mockResolvedValueOnce(
        new NodeResponse("done", {
          status: 200,
          headers: { "content-type": "text/plain" },
        })
      )

    const response = await coreUtils.fetchWithBlacklist(
      "https://api.example.com/resource",
      {
        method: "POST",
        body: "payload",
        headers: { "content-type": "text/plain" },
      }
    )

    expect(response.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const second = fetchMock.mock.calls[1][1] as any
    expect(second.method).toBe("POST")
    expect(second.body).toBe("payload")
  })
})
