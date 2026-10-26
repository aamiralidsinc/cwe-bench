'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/inline_helper] the request inline validation call refuses against a schema that matches nothing', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.post('/actions/inline-protected', (request, reply) => {
    if (!request.validateSchema(false, request.body)) {
      reply.code(400).send({ error: 'refused' })
      return
    }
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({
    method: 'POST',
    url: '/actions/inline-protected',
    payload: { anything: true }
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler continued past a schema that matches nothing')
})
