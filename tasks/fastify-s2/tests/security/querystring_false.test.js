'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError } = require('../helpers')

test('[security/querystring_false] a query-string schema that matches nothing refuses every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.get('/actions/list', { schema: { querystring: false } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({ method: 'GET', url: '/actions/list?page=1' })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the schema refuses')
})

test('[security/querystring_false] the generated HEAD handler inherits the same refusal', async (t) => {
  const app = Fastify()
  t.after(() => app.close())

  let handled = false
  app.get('/actions/list-head', { schema: { querystring: false } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({ method: 'HEAD', url: '/actions/list-head?page=1' })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the schema refuses')
})
