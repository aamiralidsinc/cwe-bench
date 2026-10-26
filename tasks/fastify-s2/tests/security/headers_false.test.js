'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/headers_false] a headers schema that matches nothing refuses every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.post('/actions/audit', { schema: { headers: false } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({
    method: 'POST',
    url: '/actions/audit',
    headers: { 'x-anything': 'value' },
    payload: {}
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the schema refuses')
})
