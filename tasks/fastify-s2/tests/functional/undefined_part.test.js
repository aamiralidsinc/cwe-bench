'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const path = require('node:path')
const { Fastify, WORKSPACE } = require('../helpers')

const { spyWarning } = require(require.resolve('process-warning', { paths: [WORKSPACE] }))
const { FSTWRN001 } = require(path.join(WORKSPACE, 'lib/warnings.js'))

test('[functional/undefined_part] an explicitly empty request part warns and still serves', async (t) => {
  const spyData = spyWarning(FSTWRN001)
  t.after(() => spyData.restore())

  const app = Fastify({ exposeHeadRoutes: false })
  t.after(() => app.close())

  let handled = 0
  app.post('/notes', { schema: { body: undefined } }, (request, reply) => {
    handled++
    reply.send({ ok: true })
  })

  const res = await app.inject({ method: 'POST', url: '/notes', payload: { text: 'hello' } })

  assert.strictEqual(res.statusCode, 200)
  assert.strictEqual(handled, 1)
  assert.strictEqual(spyData.callCount(), 1, 'the explicitly empty part must warn exactly once')
  assert.deepStrictEqual(spyData.calls[0], { arguments: ['body', 'POST', '/notes'], result: true })
})
