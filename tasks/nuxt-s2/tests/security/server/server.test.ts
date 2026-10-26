import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { existsSync } from 'node:fs'
import { join } from 'node:path'

import { buildApp, get, startApp, type RunningApp } from '../../support/server'

const FIXTURE = join(process.cwd(), '.htests/fixture')

let app: RunningApp

beforeAll(async () => {
  buildApp(FIXTURE)
  app = await startApp(FIXTURE)
}, 600_000)

afterAll(() => { app?.stop() })

describe('rules served directly for a request follow the same case rule', () => {
  it('redirects every casing of a route that has a redirect rule', async () => {
    for (const path of ['/Legacy/Home', '/legacy/home', '/LEGACY/HOME', '/lEgAcY/hOmE']) {
      const res = await get(app.base, path)
      expect(res.status, path).toBeGreaterThanOrEqual(300)
      expect(res.status, path).toBeLessThan(400)
      expect(new URL(res.location, app.base).pathname, path).toBe('/target')
    }
  })

  it('serves every casing of a route that has an ssr-off rule without the rendered page', async () => {
    for (const path of ['/secret/docs', '/SECRET/DOCS', '/Secret/Docs']) {
      const res = await get(app.base, path)
      expect(res.status, path).toBe(200)
      expect(res.body, path).not.toContain('secret-docs-marker')
    }
  })

  it('prepares the prerendered output for the route even when the rule spelling differs in case', () => {
    expect(existsSync(join(FIXTURE, '.output/public/admin/dashboard/index.html'))).toBe(true)
  })
})
