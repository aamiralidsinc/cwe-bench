'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/body_false] a request schema that matches nothing refuses every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.post('/actions/pay', { schema: { body: false } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({
    method: 'POST',
    url: '/actions/pay',
    payload: { amount: 100, to: 'someone' }
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the schema refuses')
})
