'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[functional/default_use] a server-wide default schema applies until a route overrides that part', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  app.setDefaultSchema({
    headers: { type: 'object', required: ['x-key'] }
  })

  let handled = 0
  app.post('/inherits-default', (request, reply) => {
    handled++
    reply.send({ ok: true })
  })
  app.post('/overrides-default', {
    schema: { headers: { type: 'object', required: ['x-other'] } }
  }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })

  const withKey = await app.inject({
    method: 'POST',
    url: '/inherits-default',
    headers: { 'x-key': 'k' },
    payload: {}
  })
  assert.strictEqual(withKey.statusCode, 200)
  assert.strictEqual(handled, 1)

  const withoutKey = await app.inject({
    method: 'POST',
    url: '/inherits-default',
    payload: {}
  })
  assert.ok(isClientError(withoutKey), `expected a client error, got ${withoutKey.statusCode}`)
  assert.strictEqual(handled, 1)

  const overridden = await app.inject({
    method: 'POST',
    url: '/overrides-default',
    headers: { 'x-other': 'k' },
    payload: {}
  })
  assert.strictEqual(overridden.statusCode, 200)
  assert.strictEqual(handled, 2)
})

test('[functional/default_use] a route that declares the aliased query part is not given a duplicate default', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  app.setDefaultSchema({
    querystring: { type: 'object', required: ['defaulted'] }
  })

  let handled = 0
  app.get('/alias-wins', {
    schema: { query: { type: 'object', required: ['own'] } }
  }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })

  const res = await app.inject({ method: 'GET', url: '/alias-wins?own=1' })
  assert.strictEqual(res.statusCode, 200)
  assert.strictEqual(handled, 1)
})
