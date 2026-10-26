'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/invalid_schema_value] a value that is not a schema is never silently ignored', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.post('/actions/invalid-schema', { schema: { body: null } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  let refusedAtStartup = false
  try {
    await app.ready()
  } catch (err) {
    refusedAtStartup = true
  }

  if (!refusedAtStartup) {
    const res = await app.inject({
      method: 'POST',
      url: '/actions/invalid-schema',
      payload: { anything: true }
    })
    assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
    assert.strictEqual(handled, false, 'the handler ran although its schema could not be applied')
  }
})
