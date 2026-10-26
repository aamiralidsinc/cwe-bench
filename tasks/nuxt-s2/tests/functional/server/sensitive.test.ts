import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { join } from 'node:path'

import { buildApp, get, startApp, type RunningApp } from '../../support/server'

const FIXTURE = join(process.cwd(), '.htests/fixture-sensitive')

let app: RunningApp

beforeAll(async () => {
  buildApp(FIXTURE)
  app = await startApp(FIXTURE)
}, 600_000)

afterAll(() => { app?.stop() })

describe('case-sensitive routing keeps working when the application is served', () => {
  it('still applies a rule to its exact spelling', async () => {
    const res = await get(app.base, '/Admin/Dashboard')
    expect(res.status).toBeGreaterThanOrEqual(300)
    expect(res.status).toBeLessThan(400)
    expect(new URL(res.location, app.base).pathname).toBe('/target')
  })

  it('serves a differently-cased route normally, without another spelling rule', async () => {
    const res = await get(app.base, '/admin/dashboard')
    expect(res.status).toBe(200)
    expect(res.body).toContain('sensitive-dashboard-marker')
  })
})
