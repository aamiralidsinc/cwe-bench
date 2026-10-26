import { pair, json, read, create, delay, assert, valueOf } from '../support/harness.mjs'

// The same guard covers the legacy XMLHttpRequest transport; these cases drive it directly.
export default async function ({ Backend }) {
  const cases = []
  const add = (classname, name, run) => cases.push({ classname, name, run })
  const configured = () => (req, res) => json(res, { ok: true })

  add('sec_xhr_read', 'absolute_url_value_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: '{{lng}}/{{ns}}.json' })
      const r = await read(b, 'http://127.0.0.1:' + s.bPort, 'common')
      await delay(300)
      assert(s.hitsB.length === 0, 'the legacy transport reached the host named by the value: ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_xhr_read', 'query_injection_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { loadPath: `http://127.0.0.1:${s.aPort}/locales/{{lng}}/{{ns}}.json` })
      const r = await read(b, 'en?admin=1', 'common')
      await delay(300)
      assert(s.hitsA.every((h) => !h.url.includes('admin=1')), 'the legacy transport carried the injected query: ' + valueOf(s.hitsA) + ' ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  add('sec_xhr_write', 'absolute_url_value_is_refused', async () => {
    const s = await pair(configured())
    try {
      const b = new Backend(null, { addPath: '{{lng}}/{{ns}}' })
      const r = await create(b, 'http://127.0.0.1:' + s.bPort, 'common')
      await delay(300)
      assert(s.hitsB.length === 0, 'the legacy transport sent a write to the host named by the value: ' + valueOf(r))
    } finally { await s.closeAll() }
  })

  return cases
}
