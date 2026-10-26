'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError, refusedAtStartup } = require('../helpers')

test('[security/fallback_handler] a request schema on the not-found handler refuses unmatched requests', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.setNotFoundHandler({ schema: { body: false } }, (request, reply) => {
    handled = true
    reply.code(404).send({ ok: true })
  })

  if (await refusedAtStartup(app)) {
    assert.strictEqual(handled, false)
    return
  }

  const res = await app.inject({
    method: 'POST',
    url: '/no-such-url',
    payload: { anything: true }
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the not-found handler ran for a request its schema refuses')
})

test('[security/fallback_handler] an ordinary request schema on the not-found handler is enforced too', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.setNotFoundHandler({
    schema: { body: { type: 'object', required: ['ticket'] } }
  }, (request, reply) => {
    handled = true
    reply.code(404).send({ ok: true })
  })

  if (await refusedAtStartup(app)) {
    assert.strictEqual(handled, false)
    return
  }

  const res = await app.inject({
    method: 'POST',
    url: '/no-such-url',
    payload: { other: 'value' }
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the not-found handler ran for a request its schema refuses')
})
