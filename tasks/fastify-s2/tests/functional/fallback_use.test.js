'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify } = require('../helpers')

test('[functional/fallback_use] the not-found handler still serves unmatched URLs', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  app.setNotFoundHandler((request, reply) => {
    handled++
    reply.code(404).send({ missing: true })
  })

  const res = await app.inject({ method: 'GET', url: '/unknown' })
  assert.strictEqual(res.statusCode, 404)
  assert.strictEqual(handled, 1)
})

test('[functional/fallback_use] an unmatched request that satisfies the not-found schema still reaches it', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  let hookRan = 0
  app.setNotFoundHandler({
    schema: { headers: { type: 'object', required: ['x-client'] } },
    preHandler: (request, reply, done) => {
      hookRan++
      done()
    }
  }, (request, reply) => {
    handled++
    reply.code(404).send({ missing: true })
  })

  const ok = await app.inject({
    method: 'POST',
    url: '/unknown/path',
    headers: { 'x-client': 'known' },
    payload: { anything: true }
  })
  assert.strictEqual(ok.statusCode, 404)
  assert.strictEqual(handled, 1)
  assert.strictEqual(hookRan, 1)
})
