'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify, isClientError, refusedAtStartup } = require('../helpers')

test('[security/query_alias_false] the documented alias of the query-string schema refuses every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.get('/actions/search', { schema: { query: false } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  const res = await app.inject({ method: 'GET', url: '/actions/search?q=secret' })

  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran for a request the schema refuses')
})

test('[security/query_alias_false] a route using both names is refused or enforced, never ignored', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = false
  app.get('/actions/ambiguous', { schema: { query: false, querystring: false } }, (request, reply) => {
    handled = true
    reply.send({ ok: true })
  })

  if (await refusedAtStartup(app)) {
    assert.strictEqual(handled, false)
    return
  }

  const res = await app.inject({ method: 'GET', url: '/actions/ambiguous?q=secret' })
  assert.ok(isClientError(res), `expected a client error, got ${res.statusCode}`)
  assert.strictEqual(handled, false, 'the handler ran although the schema could not be applied')
})
