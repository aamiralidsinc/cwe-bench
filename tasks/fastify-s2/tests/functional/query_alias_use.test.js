'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[functional/query_alias_use] an ordinary schema under the documented query alias still validates', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  app.get('/aliased', {
    schema: {
      query: {
        type: 'object',
        required: ['token'],
        properties: { token: { type: 'string' } }
      }
    }
  }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })

  const good = await app.inject({ method: 'GET', url: '/aliased?token=abc' })
  assert.strictEqual(good.statusCode, 200)
  assert.strictEqual(handled, 1)

  const bad = await app.inject({ method: 'GET', url: '/aliased' })
  assert.ok(isClientError(bad), `expected a client error, got ${bad.statusCode}`)
  assert.strictEqual(handled, 1)
})
