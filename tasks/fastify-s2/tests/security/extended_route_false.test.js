'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/extended_route_false] a route declared through the extended API refuses every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.route({
    method: ['POST', 'PUT'],
    url: '/actions/extended',
    schema: { body: false },
    handler: (request, reply) => {
      handled = true
      reply.send({ ok: true })
    }
  })

  const post = await app.inject({
    method: 'POST',
    url: '/actions/extended',
    payload: { anything: true }
  })
  const put = await app.inject({
    method: 'PUT',
    url: '/actions/extended',
    payload: { anything: true }
  })

  assert.ok(isClientError(post), `expected a client error for POST, got ${post.statusCode}`)
  assert.ok(isClientError(put), `expected a client error for PUT, got ${put.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the schema refuses')
})
