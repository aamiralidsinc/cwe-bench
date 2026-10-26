import { pair, json, read, readMulti, delay, assert, valueOf } from '../support/harness.mjs'

// Control task: only the advisory's own route (the reported read path) is exercised here.
export default async function ({ Backend }) {
  const cases = []
  const add = (classname, name, run) => cases.push({ classname, name, run })

  const configured = () => (req, res) => json(res, { ok: true })
  const outsidePrefix = (hits, prefix) => hits.filter((h) => !h.url.startsWith(prefix))

  add('sec_read', 'scheme_value_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: '{{lng}}/{{ns}}.json' })
      const r = await read(b, 'http:127.0.0.1:' + s.bPort, 'common')
      await delay(300)
      assert(s.hitsB.length === 0, 'a request reached the host named by the language value: ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'scheme_in_namespace_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: '{{ns}}/{{lng}}.json' })
      const r = await read(b, 'en', 'http:127.0.0.1:' + s.bPort + '/x')
      await delay(300)
      assert(s.hitsB.length === 0, 'a request reached the host named by the namespace value: ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'scheme_in_function_loadpath_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: () => '{{lng}}/{{ns}}.json' })
      const r = await read(b, 'http:127.0.0.1:' + s.bPort, 'common')
      await delay(300)
      assert(s.hitsB.length === 0, 'a configured-as-function location bypassed the check: ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'scheme_in_promise_loadpath_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: () => Promise.resolve('{{lng}}/{{ns}}.json') })
      const r = await read(b, 'http:127.0.0.1:' + s.bPort, 'common')
      await delay(300)
      assert(s.hitsB.length === 0, 'a promise-resolved location bypassed the check: ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'path_escape_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.aPort}/locales/{{lng}}/{{ns}}.json` })
      const r = await read(b, '../..', 'common')
      await delay(300)
      assert(outsidePrefix(s.hitsA, '/locales/').length === 0, 'a request left the configured path: ' + valueOf(s.hitsA) + ' ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'namespace_path_escape_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.aPort}/locales/{{lng}}/{{ns}}/data.json` })
      const r = await read(b, 'en', '../../secret')
      await delay(300)
      assert(outsidePrefix(s.hitsA, '/locales/').length === 0, 'a request left the configured path: ' + valueOf(s.hitsA) + ' ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'query_injection_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.aPort}/locales/{{lng}}/{{ns}}.json` })
      const r = await read(b, 'en?admin=1', 'common')
      await delay(300)
      assert(s.hitsA.every((h) => !h.url.includes('admin=1')), 'a request carried the injected query: ' + valueOf(s.hitsA) + ' ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_read', 'multi_load_escape_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.aPort}/locales/{{lng}}/{{ns}}.json` })
      const r = await readMulti(b, ['a', '../../..'], ['common'])
      await delay(300)
      assert(outsidePrefix(s.hitsA, '/locales/').length === 0, 'a multi-value request left the configured path: ' + valueOf(s.hitsA) + ' ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  return cases
}
