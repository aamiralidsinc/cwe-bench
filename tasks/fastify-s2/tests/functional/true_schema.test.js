'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { Fastify } = require('../helpers')

test('[functional/true_schema] a schema that matches everything keeps admitting every request', async (t) => {
  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  app.post('/open', { schema: { body: true } }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })
  app.get('/open-query', { schema: { querystring: true } }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })

  const first = await app.inject({ method: 'POST', url: '/open', payload: { anything: 1 } })
  assert.strictEqual(first.statusCode, 200)
  const second = await app.inject({ method: 'GET', url: '/open-query?whatever=1' })
  assert.strictEqual(second.statusCode, 200)
  assert.strictEqual(handled, 2)
})
