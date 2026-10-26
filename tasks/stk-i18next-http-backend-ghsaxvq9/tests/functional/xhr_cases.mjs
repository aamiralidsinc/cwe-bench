import { single, json, read, create, assert, valueOf } from '../support/harness.mjs'

// Legitimate use through the legacy XMLHttpRequest transport.
export default async function ({ Backend }) {
  const cases = []
  const add = (classname, name, run) => cases.push({ classname, name, run })

  add('func_xhr_read', 'ordinary_read_loads', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.port}/locales/{{lng}}/{{ns}}.json` })
      const r = await read(b, 'en', 'common')
      assert(!r.timeout && !r.err && r.data && r.data.ok === true, 'an ordinary read stopped working: ' + valueOf(r))
    } finally { await s.close() }
  })

  add('func_xhr_write', 'ordinary_write_is_performed', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { addPath: `http://127.0.0.1:${s.port}/add/{{lng}}/{{ns}}` })
      const r = await create(b, 'en', 'common')
      assert(!r.timeout && !r.threw, 'a legitimate write did not complete: ' + valueOf(r))
      assert(s.hits.length === 1 && s.hits[0].method === 'POST' && s.hits[0].url === '/add/en/common', 'the write changed: ' + valueOf(s.hits))
    } finally { await s.close() }
  })

  add('func_xhr_read', 'relative_custom_request_is_verbatim', async () => {
    const calls = []
    const b = new Backend(null, {
      loadPath: '{{lng}}/{{ns}}.json',
      request: (options, url, payload, callback) => {
        calls.push(url)
        callback(null, { status: 200, data: { ok: true } })
      }
    })
    const r = await read(b, 'en', 'common')
    assert(!r.timeout && !r.err && !r.threw, 'a supported location did not complete: ' + valueOf(r))
    assert(calls.length === 1 && calls[0] === 'en/common.json', 'the configured location changed: ' + valueOf(calls))
  })

  return cases
}
