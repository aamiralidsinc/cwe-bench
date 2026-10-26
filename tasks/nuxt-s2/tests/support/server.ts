import { execFileSync, spawn, type ChildProcess } from 'node:child_process'
import { createServer } from 'node:net'
import { rmSync } from 'node:fs'
import { join } from 'node:path'

const ROOT = process.cwd()

export function cleanBuild (fixture: string) {
  rmSync(join(fixture, '.output'), { recursive: true, force: true })
  rmSync(join(fixture, '.nuxt'), { recursive: true, force: true })
}

export function buildApp (fixture: string) {
  cleanBuild(fixture)
  execFileSync(process.execPath, [join(ROOT, 'node_modules/nuxt/bin/nuxt.mjs'), 'build'], {
    cwd: fixture,
    env: { ...process.env, NUXT_TELEMETRY_DISABLED: '1' },
    stdio: 'pipe',
    timeout: 540_000,
  })
}

export async function freePort (): Promise<number> {
  return await new Promise((resolve, reject) => {
    const srv = createServer()
    srv.once('error', reject)
    srv.listen(0, '127.0.0.1', () => {
      const address = srv.address()
      const port = typeof address === 'object' && address ? address.port : 0
      srv.close(() => resolve(port))
    })
  })
}

export interface RunningApp {
  base: string
  stop: () => void
}

export async function startApp (fixture: string): Promise<RunningApp> {
  const port = await freePort()
  const base = `http://127.0.0.1:${port}`
  const child: ChildProcess = spawn(process.execPath, [join(fixture, '.output/server/index.mjs')], {
    cwd: fixture,
    env: { ...process.env, PORT: String(port), HOST: '127.0.0.1', NUXT_TELEMETRY_DISABLED: '1' },
    stdio: 'pipe',
  })
  let output = ''
  child.stderr?.on('data', (chunk) => { output += String(chunk) })
  child.stdout?.on('data', (chunk) => { output += String(chunk) })
  const stop = () => { try { child.kill('SIGKILL') } catch { /* already gone */ } }

  const deadline = Date.now() + 60_000
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`server exited (${child.exitCode}) before it was ready:\n${output.slice(-4000)}`)
    }
    try {
      const res = await fetch(`${base}/`, { redirect: 'manual' })
      if (res.status > 0) { return { base, stop } }
    } catch {
      // not listening yet
    }
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  stop()
  throw new Error(`server did not become ready:\n${output.slice(-4000)}`)
}

export interface Response {
  status: number
  location: string
  body: string
}

export async function get (base: string, path: string): Promise<Response> {
  const res = await fetch(base + path, { redirect: 'manual' })
  return {
    status: res.status,
    location: res.headers.get('location') || '',
    body: await res.text(),
  }
}
