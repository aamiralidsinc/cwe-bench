'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[functional/attach_validation] a handler that asks for the validation error still receives it', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let sawError = false
  app.post('/attached', {
    attachValidation: true,
    schema: {
      body: { type: 'object', required: ['name'], properties: { name: { type: 'string' } } }
    }
  }, (request, reply) => {
    sawError = request.validationError !== undefined && request.validationError !== null
    if (sawError) {
      reply.code(400).send({ error: request.validationError.message })
      return
    }
    reply.send({ ok: true })
  })

  const good = await app.inject({ method: 'POST', url: '/attached', payload: { name: 'a' } })
  assert.strictEqual(good.statusCode, 200)
  assert.strictEqual(sawError, false)

  const bad = await app.inject({ method: 'POST', url: '/attached', payload: {} })
  assert.ok(isClientError(bad), `expected a client error, got ${bad.statusCode}`)
  assert.strictEqual(sawError, true, 'the handler did not receive the validation error it asked for')
})
