// In-process stand-in for the parts of Electron the updater uses (`net`, `session`, `app`).
//
// `net.request` follows Electron 39's ClientRequest redirect semantics
// (lib/common/api/net-client-request.ts and shell/common/api/electron_api_url_loader.cc):
//   - a 'redirect' event is emitted in both 'follow' and 'manual' mode;
//   - 'manual': the redirect is cancelled with an error unless followRedirect() is called
//     synchronously in the event, or the request is aborted;
//   - 'follow' (the default): the redirect is followed unless the request was aborted in the event;
//   - a followed redirect re-sends the same request headers to the new URL (the network service
//     does not drop credential headers);
//   - abort() emits 'abort' on the next tick and nothing else.
// Hosts are virtual: each origin is served by a handler registered by the test, and every
// request that reaches an origin is recorded with its headers. No sockets are opened.
import { EventEmitter } from "node:events"
import { Readable } from "node:stream"

export interface SeenRequest {
  origin: string
  path: string
  method: string
  headers: Record<string, string>
}

export interface FakeResponse {
  status: number
  headers?: Record<string, string>
  body?: Buffer | string
}

export type OriginHandler = (req: SeenRequest) => FakeResponse

interface NetState {
  origins: Map<string, OriginHandler>
  seen: Array<SeenRequest>
  app: { version: string; userData: string }
}

const STATE_KEY = Symbol.for("cwe-bench.fake-electron")
const g = globalThis as any
if (g[STATE_KEY] == null) {
  g[STATE_KEY] = { origins: new Map(), seen: [], app: { version: "1.0.0", userData: "/tmp" } } satisfies NetState
}
const state: NetState = g[STATE_KEY]

export function serve(origin: string, handler: OriginHandler): void {
  state.origins.set(new URL(origin).origin, handler)
}

export function resetNet(): void {
  state.origins.clear()
  state.seen.length = 0
}

export function seenRequests(): Array<SeenRequest> {
  return state.seen.slice()
}

export function setAppInfo(version: string, userData: string): void {
  state.app.version = version
  state.app.userData = userData
}

function headerValue(v: unknown): string {
  return Array.isArray(v) ? v.join(", ") : String(v)
}

class FakeClientRequest extends EventEmitter {
  private aborted = false
  private finished = false
  private followCb: (() => void) | null = null
  private readonly policy: string
  private readonly method: string
  private readonly headers: Record<string, string> = {}

  constructor(private url: URL, options: any) {
    super()
    this.policy = options.redirect ?? "follow"
    this.method = String(options.method ?? "GET").toUpperCase()
    for (const [k, v] of Object.entries(options.headers ?? {})) {
      if (v != null) {
        this.headers[k.toLowerCase()] = headerValue(v)
      }
    }
  }

  setHeader(name: string, value: unknown): void {
    this.headers[name.toLowerCase()] = headerValue(value)
  }

  getHeader(name: string): string | undefined {
    return this.headers[name.toLowerCase()]
  }

  write(): boolean {
    return true
  }

  end(): this {
    if (!this.finished) {
      this.finished = true
      setImmediate(() => this.dispatch(this.url, 0))
    }
    return this
  }

  abort(): void {
    if (!this.aborted) {
      process.nextTick(() => this.emit("abort"))
    }
    this.aborted = true
  }

  followRedirect(): void {
    if (this.followCb == null) {
      throw new Error("followRedirect() called outside of a 'redirect' event")
    }
    this.followCb()
  }

  private fail(message: string): void {
    if (!this.aborted) {
      this.aborted = true
      this.emit("error", new Error(message))
    }
  }

  private dispatch(url: URL, hops: number): void {
    if (this.aborted) {
      return
    }
    if (hops > 20) {
      this.fail("net::ERR_TOO_MANY_REDIRECTS")
      return
    }
    const handler = state.origins.get(url.origin)
    const seen: SeenRequest = { origin: url.origin, path: url.pathname + url.search, method: this.method, headers: { ...this.headers } }
    if (handler == null) {
      this.fail(`net::ERR_NAME_NOT_RESOLVED (${url.origin})`)
      return
    }
    state.seen.push(seen)
    let res: FakeResponse
    try {
      res = handler(seen)
    } catch (e: any) {
      res = { status: 500, body: String(e?.message ?? e) }
    }
    const resHeaders: Record<string, string> = {}
    for (const [k, v] of Object.entries(res.headers ?? {})) {
      resHeaders[k.toLowerCase()] = v
    }

    const location = resHeaders["location"]
    if (res.status >= 300 && res.status < 400 && location != null) {
      const next = new URL(location, url)
      if (this.policy === "error") {
        this.fail("Attempted to redirect, but redirect policy was 'error'")
        return
      }
      let followed = false
      this.followCb = this.policy === "manual" ? () => (followed = true) : () => {}
      const headerArrays: Record<string, string[]> = {}
      for (const [k, v] of Object.entries(resHeaders)) {
        headerArrays[k] = [v]
      }
      try {
        this.emit("redirect", res.status, this.method, next.href, headerArrays)
      } finally {
        this.followCb = null
      }
      if (this.aborted) {
        return
      }
      if (this.policy === "manual" && !followed) {
        this.fail("Redirect was cancelled")
        return
      }
      this.url = next
      this.dispatch(next, hops + 1)
      return
    }

    const body = res.body == null ? Buffer.alloc(0) : Buffer.isBuffer(res.body) ? res.body : Buffer.from(res.body)
    const response: any = Readable.from(body.length === 0 ? [] : [body], { objectMode: false })
    response.statusCode = res.status
    response.statusMessage = res.status < 400 ? "OK" : "Error"
    response.headers = { "content-length": String(body.length), ...resHeaders }
    this.emit("response", response)
  }
}

export const fakeElectron = {
  net: {
    request(options: any): FakeClientRequest {
      let url: URL
      if (typeof options === "string") {
        url = new URL(options)
        options = {}
      } else if (options.url != null) {
        url = new URL(options.url)
      } else {
        const protocol = options.protocol || "https:"
        const host = options.host || `${options.hostname}${options.port ? `:${options.port}` : ""}`
        url = new URL(`${protocol}//${host}${options.path || "/"}`)
      }
      return new FakeClientRequest(url, options)
    },
  },
  session: {
    fromPartition(): object {
      return {}
    },
  },
  app: {
    get isPackaged(): boolean {
      return true
    },
    getVersion: (): string => state.app.version,
    getName: (): string => "credential-test-app",
    getAppPath: (): string => state.app.userData,
    getPath: (): string => state.app.userData,
    whenReady: (): Promise<void> => Promise.resolve(),
    on(): void {},
    once(): void {},
    quit(): void {},
    relaunch(): void {},
  },
  autoUpdater: new EventEmitter(),
  Notification: class {
    show(): void {}
  },
}
