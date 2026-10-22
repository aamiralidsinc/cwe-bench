// Shared harness for the hidden tests. It drives the product through its real
// public surfaces only:
//   - the test-runner API WebSocket server (created by the product when the
//     server is configured), spoken to with a minimal birpc client exactly as
//     the product's own UI client does;
//   - the browser-mode file command functions, invoked as the command
//     dispatcher invokes them, with the browser project the runner itself
//     resolves and initialises from its configuration;
//   - the HTTP endpoints those servers expose, with a real fetch.
//
// Nothing here imports the hidden expectations; every expected value and
// cleanup is computed in the test itself.
import { createBirpc } from 'birpc'
import { parse, stringify } from 'flatted'
import { promises as fs } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { WebSocket } from 'ws'
import { createVitest } from 'vitest/node'
import { preview } from '@vitest/browser-preview'

const API_PATH = '/__vitest_api__'
const ATTACHMENT_PATH = '/__vitest_attachment__'

// The runner installs a process-level unhandledRejection handler that calls
// process.exit. These tests embed the runner inside the verifier process, so a
// rejection raised by one of its fire-and-forget internals must not take the
// whole suite down. Swap in a recording no-op before any server is created.
const rejections: unknown[] = []
function neutralizeProcessExitOnRejection(): void {
  for (const listener of process.listeners('unhandledRejection')) {
    process.off('unhandledRejection', listener)
  }
  process.on('unhandledRejection', (err) => { rejections.push(err) })
}
neutralizeProcessExitOnRejection()

export interface UiHandle {
  server: any
  root: string
  file: string
  rpc: any
  ws: WebSocket
  port: number
  token: string
  rerunFilesCalls: string[][]
  rerunTaskCalls: string[]
  updateSnapshotCalls: unknown[][]
  close: () => Promise<void>
}

export interface BrowserHandle {
  server: any
  project: any
  root: string
  port: number | undefined
  token: string
  close: () => Promise<void>
}

// Start the real runner with its network API enabled on `host`. When `ui` is
// set the product mounts its UI middleware (including the attachment endpoint).
// When `fsStrict` is false the project opts out of Vite's strict file serving
// through a normal config file, and the browser project `extends` that file so
// every vite the product brings up sees the same setting. `api` may be given as
// a bare port number to cover that input shape.
export async function startUi(
  host: string | undefined,
  opts: { ui?: boolean, api?: number | { port?: number, host?: string }, fsStrict?: boolean } = {},
): Promise<UiHandle> {
  const api = opts.api !== undefined
    ? opts.api
    : { port: 0, ...(host === undefined ? {} : { host }) }
  const root = await fs.mkdtemp(join(tmpdir(), 'vitest-ui-root-'))
  let config: string | false = false
  if (opts.fsStrict === false) {
    config = join(root, 'vitest.config.ts')
    await fs.writeFile(config, 'export default { server: { fs: { strict: false } } }\n', 'utf-8')
  }
  const server: any = await createVitest('test', {
    root,
    config,
    api: api as any,
    watch: true,
    ui: opts.ui ?? false,
  }, opts.fsStrict === false ? { server: { fs: { strict: false } } } : {})
  neutralizeProcessExitOnRejection()

  // The sample test file lives outside the project root so the watcher the
  // runner starts for `watch: true` never sees it; the API is what writes it.
  const file = join(await fs.mkdtemp(join(tmpdir(), 'vitest-ui-')), 'sample.test.ts')
  await fs.writeFile(file, 'export const original = true\n', 'utf-8')
  server.state.filesMap.set(file, [])

  const rerunFilesCalls: string[][] = []
  const rerunTaskCalls: string[] = []
  server.rerunFiles = async (files: string[]) => { rerunFilesCalls.push(files) }
  server.rerunTask = async (id: string) => { rerunTaskCalls.push(id) }
  const updateSnapshotCalls: unknown[][] = []
  server.updateSnapshot = async (...args: unknown[]) => { updateSnapshotCalls.push(args) }

  const { port, token } = server.config.api
  // A binding of localhost or an unset host can land on ::1 (IPv6) while
  // 'localhost' may resolve to 127.0.0.1 first. Ask the live server where it
  // actually is and connect to that.
  const addr = server.vite?.httpServer?.address?.()
  let connectHost: string
  let connectPort: number = port
  if (addr && typeof addr === 'object') {
    connectPort = addr.port
    if (addr.address === '::' || addr.address === '0.0.0.0') {
      connectHost = '127.0.0.1'
    } else if (addr.address === '::1') {
      connectHost = '[::1]'
    } else {
      connectHost = addr.address
    }
  } else {
    connectHost = host === undefined || host === 'localhost' ? 'localhost' : '127.0.0.1'
  }
  const ws = new WebSocket(`ws://${connectHost}:${connectPort}${API_PATH}?token=${token ?? ''}`)
  await new Promise<void>((resolve, reject) => {
    ws.on('open', () => resolve())
    ws.on('error', reject)
  })
  const rpc: any = createBirpc({}, {
    post: (msg: any) => ws.send(msg),
    on: (fn: any) => ws.on('message', (d: any) => fn(d.toString())),
    serialize: (data: any) => stringify(data),
    deserialize: (data: any) => parse(data),
    timeout: 8000,
  })
  return {
    server, root, file, rpc, ws, port, token: token ?? '', rerunFilesCalls, rerunTaskCalls, updateSnapshotCalls,
    close: async () => { try { ws.close() } catch {} ; await server.close() },
  }
}

// Start the runner with a browser-mode project and bring up its browser
// server, exactly as a browser test run does before it dispatches file
// commands. Both the runner API and the browser API follow `host`. The preview
// provider is used so no real browser is launched. When `inheritApi` is false
// the browser project gets its own `browser.api` binding. When `unsetBrowserApi`
// is set the browser project is given no `browser.api` at all, so whatever the
// product does with an unconfigured binding is what the test observes.
export async function startBrowserProject(
  host: string | undefined,
  opts: { fsStrict?: boolean, inheritApi?: boolean, unsetBrowserApi?: boolean } = {},
): Promise<BrowserHandle> {
  const root = await fs.mkdtemp(join(tmpdir(), 'vitest-cmd-'))
  const config = join(root, 'vitest.config.ts')
  const strict = opts.fsStrict === false ? 'false' : 'true'
  await fs.writeFile(config, `export default { server: { fs: { strict: ${strict} } } }\n`, 'utf-8')
  const browserApi = opts.unsetBrowserApi
    ? {}
    : opts.inheritApi === false
      ? { api: { port: 0, host: '127.0.0.1' } }
      : host === undefined
        ? {}
        : { api: { host } }

  const server: any = await createVitest('test', {
    root,
    config,
    watch: false,
    api: { port: 0, ...(host === undefined ? {} : { host }) },
  } as any, {
    test: {
      projects: [{
        extends: config,
        test: {
          name: 'browser',
          browser: {
            enabled: true,
            headless: true,
            provider: preview(),
            instances: [{ browser: 'chromium' }],
            ...browserApi,
          },
        },
      }],
    },
  } as any)
  neutralizeProcessExitOnRejection()

  await server._initBrowserServers()
  const project = server.projects.find((p: any) => p.browser)
  if (!project) {
    await server.close()
    throw new Error('browser project was not initialised')
  }
  const bvite = project.browser?.vite
  return {
    server,
    project,
    root,
    port: bvite?.config?.server?.port ?? bvite?.httpServer?.address?.()?.port,
    token: server.config.api.token ?? '',
    close: async () => { await server.close() },
  }
}

// Real HTTP GET against the browser server's attachment endpoint.
export async function fetchBrowserAttachment(
  handle: BrowserHandle,
  path: string,
): Promise<{ status: number, body: string }> {
  const url = `http://127.0.0.1:${handle.port}${ATTACHMENT_PATH}`
    + `?path=${encodeURIComponent(path)}&contentType=text/plain&token=${handle.token}`
  const res = await fetch(url)
  return { status: res.status, body: await res.text() }
}

// Real HTTP request against the UI server's attachment endpoint.
export async function fetchUiAttachment(
  handle: UiHandle,
  path: string,
  init: { method: 'GET' | 'POST', body?: string } = { method: 'GET' },
): Promise<{ status: number, body: string }> {
  const url = `http://127.0.0.1:${handle.port}${ATTACHMENT_PATH}`
    + `?path=${encodeURIComponent(path)}&contentType=text/plain&token=${handle.token}`
  const res = await fetch(url, { method: init.method, body: init.body })
  return { status: res.status, body: await res.text() }
}

export async function readIfExists(path: string): Promise<string | null> {
  try { return await fs.readFile(path, 'utf-8') }
  catch { return null }
}

export async function exists(path: string): Promise<boolean> {
  try { await fs.access(path); return true }
  catch { return false }
}
