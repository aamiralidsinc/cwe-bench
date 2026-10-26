'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/custom_compiler] a custom validator compiler receives and enforces a schema that matches nothing', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  const received = []
  let handled = false

  app.post('/actions/custom-compiler', {
    schema: { body: false },
    validatorCompiler: ({ schema, httpPart }) => {
      received.push({ schema, httpPart })
      const validate = () => {
        validate.errors = [{ message: 'denied by the compiled schema' }]
        return false
      }
      return validate
    }
  }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  await app.ready()

  assert.strictEqual(received.length, 1, 'the custom compiler was not asked to compile the request schema')
  assert.strictEqual(received[0].schema, false, 'the custom compiler did not receive the schema unchanged')

  const res = await app.inject({
    method: 'POST',
    url: '/actions/custom-compiler',
    payload: { anything: true }
  })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the custom compiler refuses')
})
