'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/default_schema] a server-wide default schema that matches nothing refuses every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  app.setDefaultSchema({ body: false })

  let handled = false
  app.post('/actions/default-protected', (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({
    method: 'POST',
    url: '/actions/default-protected',
    payload: { anything: true }
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the default schema refuses')
})
