import { single, json, read, readMulti, create, delay, assert, valueOf } from '../support/harness.mjs'

// Legitimate configurations and values that must keep working exactly as today.
export default async function ({ Backend }) {
  const cases = []
  const add = (classname, name, run) => cases.push({ classname, name, run })

  const spy = () => {
    const calls = []
    const request = (options, url, payload, callback) => {
      calls.push({ url, payload })
      callback(null, { status: 200, data: { ok: true } })
    }
    return { calls, request }
  }

  add('func_read', 'relative_default_is_requested_verbatim', async () => {
    const s = spy()
    const b = new Backend(null, { request: s.request })
    const r = await read(b, 'en', 'common')
    assert(!r.timeout && !r.err && !r.threw, 'a legitimate read did not complete: ' + valueOf(r))
    assert(s.calls.length === 1 && s.calls[0].url === '/locales/en/common.json', 'the default location changed: ' + valueOf(s.calls))
    assert(s.calls[0].payload === undefined, 'a read sent a payload: ' + valueOf(s.calls[0].payload))
  })

  add('func_read', 'leading_placeholders_with_safe_values_are_requested', async () => {
    const s = spy()
    const b = new Backend(null, { loadPath: '{{lng}}/{{ns}}.json', request: s.request })
    const r = await read(b, 'en', 'common')
    assert(!r.timeout && !r.err && !r.threw, 'a supported location did not complete: ' + valueOf(r))
    assert(s.calls.length === 1 && s.calls[0].url === 'en/common.json', 'the configured location changed: ' + valueOf(s.calls))
  })

  add('func_read', 'custom_path_is_handed_over_verbatim', async () => {
    const s = spy()
    const b = new Backend(null, { loadPath: '/some/crazy/{{lng}}/{{ns}}/path', request: s.request })
    const r = await read(b, 'de', 'testns')
    assert(!r.timeout && !r.err && !r.threw, 'a legitimate read did not complete: ' + valueOf(r))
    assert(s.calls[0] && s.calls[0].url === '/some/crazy/de/testns/path', 'the URL was rewritten: ' + valueOf(s.calls))
  })

  add('func_read', 'falsy_location_still_returns_empty', async () => {
    const s = spy()
    const b = new Backend(null, { loadPath: () => '', request: s.request })
    const r = await read(b, 'en', 'common')
    assert(!r.timeout && !r.err && !r.threw, 'a disabled location did not complete: ' + valueOf(r))
    assert(s.calls.length === 0, 'a disabled location still made a request: ' + valueOf(s.calls))
    assert(r.data && typeof r.data === 'object' && Object.keys(r.data).length === 0, 'a disabled location did not resolve empty: ' + valueOf(r.data))
  })

  add('func_read', 'function_location_still_loads', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { loadPath: () => `http://127.0.0.1:${s.port}/locales/{{lng}}/{{ns}}.json` })
      const r = await read(b, 'en', 'common')
      assert(!r.timeout && !r.err && r.data && r.data.ok === true, 'a function location stopped working: ' + valueOf(r))
    } finally { await s.close() }
  })

  add('func_read', 'promise_location_still_loads', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { loadPath: () => Promise.resolve(`http://127.0.0.1:${s.port}/locales/{{lng}}/{{ns}}.json`) })
      const r = await read(b, 'en', 'common')
      assert(!r.timeout && !r.err && r.data && r.data.ok === true, 'a promise location stopped working: ' + valueOf(r))
    } finally { await s.close() }
  })

  add('func_read', 'multi_load_joins_values', async () => {
    const s = spy()
    const b = new Backend(null, { loadPath: '/locales/{{lng}}/{{ns}}.json', request: s.request })
    const r = await readMulti(b, ['en', 'de'], ['common', 'extra'])
    assert(!r.timeout && !r.err && !r.threw, 'a multi load did not complete: ' + valueOf(r))
    assert(s.calls.length === 1 && s.calls[0].url === '/locales/en+de/common+extra.json', 'the multi-value join changed: ' + valueOf(s.calls))
  })

  add('func_read', 'language_tag_with_region_is_requested', async () => {
    const s = spy()
    const b = new Backend(null, { loadPath: '/locales/{{lng}}/{{ns}}.json', request: s.request })
    const r = await read(b, 'zh-Hant-TW', 'common')
    assert(!r.timeout && !r.err && !r.threw, 'a regional language tag did not complete: ' + valueOf(r))
    assert(s.calls[0] && s.calls[0].url === '/locales/zh-Hant-TW/common.json', 'a regional language tag changed the URL: ' + valueOf(s.calls))
  })

  add('func_read', 'query_parameters_are_still_appended', async () => {
    const s = await single((req, res) => {
      const parsed = new URL(req.url, 'http://127.0.0.1')
      json(res, Object.fromEntries(parsed.searchParams.entries()))
    })
    try {
      const b = new Backend(null, {
        loadPath: `http://127.0.0.1:${s.port}/locales/{{lng}}/{{ns}}.json`,
        queryStringParams: { version: '1.2.3' }
      })
      const r = await read(b, 'en', 'common')
      assert(!r.timeout && !r.err && r.data && r.data.version === '1.2.3', 'query parameters stopped working: ' + valueOf(r))
    } finally { await s.close() }
  })

  add('func_read', 'no_redirect_request_still_loads', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.port}/locales/{{lng}}/{{ns}}.json` })
      const r = await read(b, 'en', 'common')
      assert(!r.timeout && !r.err && r.data && r.data.ok === true, 'an ordinary read stopped working: ' + valueOf(r))
    } finally { await s.close() }
  })

  add('func_read', 'alternate_fetch_is_still_used', async () => {
    let seen = null
    const b = new Backend(null, {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
      alternateFetch: (url, init) => {
        seen = { url, init }
        return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('{"ok":true}') })
      }
    })
    const r = await read(b, 'en', 'common')
    assert(!r.timeout && !r.err && r.data && r.data.ok === true, 'an app-supplied transport stopped working: ' + valueOf(r))
    assert(seen && seen.url === '/locales/en/common.json', 'the app-supplied transport received a different URL: ' + valueOf(seen && seen.url))
  })

  add('func_write', 'write_is_still_performed', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { addPath: `http://127.0.0.1:${s.port}/add/{{lng}}/{{ns}}` })
      const r = await create(b, 'en', 'common')
      assert(!r.timeout && !r.threw, 'a legitimate write did not complete: ' + valueOf(r))
      assert(s.hits.length === 1 && s.hits[0].method === 'POST' && s.hits[0].url === '/add/en/common', 'the write changed: ' + valueOf(s.hits))
      assert(s.hits[0].body === '{"key":"value"}', 'the write payload changed: ' + valueOf(s.hits[0].body))
    } finally { await s.close() }
  })

  add('func_write', 'leading_placeholders_with_safe_values_are_written', async () => {
    const s = spy()
    const b = new Backend(null, { addPath: '{{lng}}/{{ns}}', request: s.request })
    const r = await create(b, 'en', 'common')
    assert(!r.timeout && !r.threw, 'a supported write did not complete: ' + valueOf(r))
    assert(s.calls.length === 1 && s.calls[0].url === 'en/common', 'the configured write location changed: ' + valueOf(s.calls))
    assert(s.calls[0].payload && s.calls[0].payload.key === 'value', 'the write payload changed: ' + valueOf(s.calls[0].payload))
  })

  add('func_write', 'function_location_is_still_used', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { addPath: (lng, ns) => `http://127.0.0.1:${s.port}/add/` + lng + '/' + ns })
      const r = await create(b, 'en', 'common')
      assert(!r.timeout && !r.threw, 'a function write location did not complete: ' + valueOf(r))
      assert(s.hits.length === 1 && s.hits[0].url === '/add/en/common', 'a function write location changed: ' + valueOf(s.hits))
    } finally { await s.close() }
  })

  add('func_write', 'no_redirect_write_still_works', async () => {
    const s = await single((req, res) => json(res, { ok: true }))
    try {
      const b = new Backend(null, { addPath: `http://127.0.0.1:${s.port}/add/{{lng}}/{{ns}}` })
      const r = await create(b, 'en', 'common')
      assert(!r.timeout && !r.threw && s.hits.length === 1, 'an ordinary write stopped working: ' + valueOf(r))
    } finally { await s.close() }
  })

  return cases
}
