'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[functional/inline_helper_use] the request inline validation call still validates ordinary schemas', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  app.post('/inline', (request, reply) => {
    if (!request.validateSchema({ type: 'object', required: ['name'] }, request.body)) {
      reply.code(400).send({ error: 'invalid' })
      return
    }
    handled++
    reply.send({ ok: true })
  })

  const good = await app.inject({ method: 'POST', url: '/inline', payload: { name: 'n' } })
  assert.strictEqual(good.statusCode, 200)
  assert.strictEqual(handled, 1)

  const bad = await app.inject({ method: 'POST', url: '/inline', payload: {} })
  assert.ok(isClientError(bad), `expected a client error, got ${bad.statusCode}`)
  assert.strictEqual(handled, 1)
})

test('[functional/inline_helper_use] the request inline validation call accepts an absent schema', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let accepted
  app.post('/inline-absent', (request, reply) => {
    accepted = request.validateSchema(undefined, request.body)
    reply.send({ accepted })
  })

  const res = await app.inject({ method: 'POST', url: '/inline-absent', payload: { anything: 1 } })
  assert.strictEqual(res.statusCode, 200)
  assert.strictEqual(accepted, true)
})
