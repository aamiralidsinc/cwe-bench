// Shared harness for the hidden tests. It drives the product through its real
// public surfaces only:
//   - the test-runner API WebSocket server (created by the product when the
//     server is configured), spoken to with a minimal birpc client exactly as
//     the product's own UI client does;
//   - the browser-mode API WebSocket server, spoken to as the product's
//     browser orchestrator does: a session is created through the runner's own
//     session registry and the file operations are requested with the same
//     command call the browser client sends.
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
const BROWSER_API_PATH = '/__vitest_browser_api__'

export interface UiHandle {
  server: any
  file: string
  rpc: any
  ws: WebSocket
  rerunFilesCalls: string[][]
  rerunTaskCalls: string[]
  updateSnapshotCalls: unknown[][]
  close: () => Promise<void>
}

// Start the real runner with its network API enabled on `host`, register one
// on-disk test file (so handlers that require a known file proceed), and open
// a client connection holding the server's own token.
export async function startUi(host: string): Promise<UiHandle> {
  const root = await fs.mkdtemp(join(tmpdir(), 'vitest-ui-root-'))
  const server: any = await createVitest(
    'test',
    { root, api: { port: 0, host }, watch: true },
    {},
  )
  const file = join(root, 'sample.test.ts')
  await fs.writeFile(file, 'export const original = true\n', 'utf-8')
  server.state.filesMap.set(file, [])

  const rerunFilesCalls: string[][] = []
  const rerunTaskCalls: string[] = []
  server.rerunFiles = async (files: string[]) => { rerunFilesCalls.push(files) }
  server.rerunTask = async (id: string) => { rerunTaskCalls.push(id) }
  const updateSnapshotCalls: unknown[][] = []
  server.updateSnapshot = async (...args: unknown[]) => { updateSnapshotCalls.push(args) }

  const { token } = server.config.api
  // Vite may fall back to another port when the configured one is still
  // being released by a previous test, so connect to the bound port.
  const address = server.vite.httpServer.address()
  const port = typeof address === 'object' && address ? address.port : server.config.api.port
  const ws = new WebSocket(`ws://127.0.0.1:${port}${API_PATH}?token=${token ?? ''}`)
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
    server, file, rpc, ws, rerunFilesCalls, rerunTaskCalls, updateSnapshotCalls,
    close: async () => {
      try { ws.close() } catch {}
      await server.close()
      await fs.rm(root, { recursive: true, force: true }).catch(() => {})
    },
  }
}

let browserSessions = 0

export interface BrowserHandle {
  project: any
  root: string
  rpc: any
  sessionId: string
  close: () => Promise<void>
}

// Start the runner with a browser-mode project and bring up its browser API
// server, exactly as a browser test run does. Both the runner API and the
// browser API are bound to `host`. The preview provider is used so no real
// browser is launched. A client then connects to the browser API WebSocket as
// the orchestrator does, and file commands are requested through the same
// `triggerCommand` call the browser client uses.
export async function startBrowserProject(
  host: string,
  options: { relaxedFileServing?: boolean, rootHost?: string } = {},
): Promise<BrowserHandle> {
  const root = await fs.mkdtemp(join(tmpdir(), 'vitest-cmd-'))
  // The runner's own control server and the browser-mode server are separate
  // servers; each may bind to its own address.
  const rootHost = options.rootHost ?? host
  const server: any = await createVitest(
    'test',
    { root, watch: false, api: { port: 0, host: rootHost } },
    {
      test: {
        projects: [{
          // A project may configure the server to serve files outside its
          // root; the control API's own file operations must still not do so.
          ...(options.relaxedFileServing
            ? { server: { fs: { strict: false } } }
            : {}),
          test: {
            name: 'browser',
            browser: {
              enabled: true,
              // The preview provider opens a page only when a test actually
              // asks for one; it rejects headless mode at construction.
              headless: false,
              provider: preview(),
              instances: [{ browser: 'chromium' }],
              api: { host },
            },
          },
        }],
      },
    } as any,
  )
  await server._initBrowserServers()
  const project = server.projects.find((p: any) => p.browser)
  if (!project) {
    await server.close()
    throw new Error('browser project was not initialised')
  }
  await project.browser.initBrowserProvider(project)

  const sessionId = `verifier-session-${++browserSessions}`
  const sessions = server._browserSessions
  sessions.sessionIds.add(sessionId)
  // createSession resolves when the orchestrator connection is accepted; a
  // failure only means this test cannot ask the product anything, so surface
  // it to the caller instead of leaving it unhandled.
  const sessionPromise = sessions.createSession(sessionId, project, {
    reject: () => {},
  })
  sessionPromise.catch(() => {})

  const address = project.browser.vite.httpServer.address()
  const url = `ws://127.0.0.1:${address.port}${BROWSER_API_PATH}`
    + `?type=orchestrator&rpcId=verifier-rpc-${browserSessions}`
    + `&sessionId=${encodeURIComponent(sessionId)}`
    + `&projectName=${encodeURIComponent(project.name)}`
    + `&token=${server.config.api.token ?? ''}`
  const ws = new WebSocket(url)
  await new Promise<void>((resolve, reject) => {
    ws.on('open', () => resolve())
    ws.on('error', reject)
  })
  await sessionPromise
  const rpc: any = createBirpc({}, {
    post: (msg: any) => ws.send(msg),
    on: (fn: any) => ws.on('message', (d: any) => fn(d.toString())),
    serialize: (data: any) => stringify(data),
    deserialize: (data: any) => parse(data),
    timeout: 8000,
  })
  return {
    project,
    root,
    rpc,
    sessionId,
    close: async () => {
      try { ws.close() } catch {}
      sessions.destroySession(sessionId)
      await server.close()
      await fs.rm(root, { recursive: true, force: true }).catch(() => {})
    },
  }
}

// Register one test entity with the runner's own collection state, exactly as
// the product does when a test file is collected, so operations that act on a
// test can be exercised from the client side. Returns the test's id.
export function seedTest(browser: BrowserHandle): string {
  const { project, root } = browser
  const filepath = join(root, 'sample.test.ts')
  const fileTask: any = {
    id: `${project.name}:sample.test.ts`,
    name: 'sample.test.ts',
    fullName: 'sample.test.ts',
    type: 'suite',
    mode: 'run',
    filepath,
    tasks: [],
    meta: Object.create(null),
    projectName: project.name,
  }
  fileTask.file = fileTask
  const testTask: any = {
    id: `${project.name}:sample.test.ts:test`,
    name: 'sample',
    fullName: 'sample.test.ts > sample',
    type: 'test',
    mode: 'run',
    file: fileTask,
    tasks: [],
    meta: Object.create(null),
    annotations: [],
    artifacts: [],
  }
  fileTask.tasks.push(testTask)
  project.vitest.state.collectFiles(project, [fileTask])
  return testTask.id
}

export async function readIfExists(path: string): Promise<string | null> {
  try { return await fs.readFile(path, 'utf-8') }
  catch { return null }
}
