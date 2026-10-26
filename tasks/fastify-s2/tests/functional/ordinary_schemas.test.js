'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[functional/ordinary_schemas] ordinary request schemas still accept and refuse the same requests', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  const handler = (request, reply) => {
    handled++
    reply.send({ ok: true })
  }

  app.post('/orders/:id', {
    schema: {
      params: { type: 'object', required: ['id'], properties: { id: { type: 'string' } } },
      headers: { type: 'object', required: ['x-api-key'] },
      querystring: { type: 'object', required: ['mode'] },
      body: {
        type: 'object',
        required: ['amount'],
        properties: { amount: { type: 'integer' } }
      }
    }
  }, handler)

  const good = await app.inject({
    method: 'POST',
    url: '/orders/abc?mode=fast',
    headers: { 'x-api-key': 'k' },
    payload: { amount: 2 }
  })
  assert.strictEqual(good.statusCode, 200)
  assert.strictEqual(handled, 1)

  const badBody = await app.inject({
    method: 'POST',
    url: '/orders/abc?mode=fast',
    headers: { 'x-api-key': 'k' },
    payload: { amount: 'two' }
  })
  assert.ok(isClientError(badBody), `expected a client error, got ${badBody.statusCode}`)
  assert.strictEqual(handled, 1)

  const badHeader = await app.inject({
    method: 'POST',
    url: '/orders/abc?mode=fast',
    payload: { amount: 2 }
  })
  assert.ok(isClientError(badHeader), `expected a client error, got ${badHeader.statusCode}`)
  assert.strictEqual(handled, 1)
})

test('[functional/ordinary_schemas] a querystring schema keeps validating the query string', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  app.get('/reports', {
    schema: { querystring: { type: 'object', required: ['from'], properties: { from: { type: 'string' } } } }
  }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })

  const good = await app.inject({ method: 'GET', url: '/reports?from=now' })
  assert.strictEqual(good.statusCode, 200)
  const bad = await app.inject({ method: 'GET', url: '/reports' })
  assert.ok(isClientError(bad), `expected a client error, got ${bad.statusCode}`)
  assert.strictEqual(handled, 1)
})
