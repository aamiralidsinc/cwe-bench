import http from 'node:http'

function listen (handler) {
  return new Promise((resolve, reject) => {
    const server = http.createServer(handler)
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => resolve(server))
  })
}

function close (server) {
  return new Promise((resolve) => {
    try { server.closeAllConnections() } catch (_) {}
    try { server.close(() => resolve()) } catch (_) { resolve() }
    setTimeout(resolve, 200)
  })
}

export function json (res, body) {
  res.writeHead(200, { 'content-type': 'application/json', connection: 'close' })
  res.end(JSON.stringify(body))
}

// A configured ("allowed") server plus a foreign server. handlerA receives
// (req, res, { bPort }) and answers the configured destination.
export async function pair (handlerA) {
  const hitsA = []
  const hitsB = []
  const b = await listen((req, res) => {
    hitsB.push({ method: req.method, url: req.url })
    json(res, { attacker: true })
  })
  const bPort = b.address().port
  const a = await listen((req, res) => {
    hitsA.push({ method: req.method, url: req.url })
    handlerA(req, res, { bPort })
  })
  return {
    a,
    b,
    aPort: a.address().port,
    bPort,
    hitsA,
    hitsB,
    closeAll: async () => { await close(a); await close(b) }
  }
}

export async function single (handler) {
  const hits = []
  const server = await listen((req, res) => {
    const chunks = []
    req.on('data', (c) => chunks.push(c))
    req.on('end', () => {
      hits.push({ method: req.method, url: req.url, body: Buffer.concat(chunks).toString() })
      handler(req, res)
    })
  })
  return {
    server,
    port: server.address().port,
    hits,
    close: () => close(server)
  }
}

export function delay (ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function assert (condition, message) {
  if (!condition) throw new Error(message)
}

function settle (starter, timeout) {
  return new Promise((resolve) => {
    let done = false
    const finish = (value) => {
      if (done) return
      done = true
      clearTimeout(timer)
      resolve(value)
    }
    const timer = setTimeout(() => finish({ timeout: true }), timeout)
    try {
      starter((err, data) => finish({ err: err && (err.message || String(err)), data }))
    } catch (e) {
      finish({ threw: String((e && (e.message || e)) || e) })
    }
  })
}

export function read (backend, language, namespace, timeout = 8000) {
  return settle((cb) => backend.read(language, namespace, cb), timeout)
}

export function readMulti (backend, languages, namespaces, timeout = 8000) {
  return settle((cb) => backend.readMulti(languages, namespaces, cb), timeout)
}

// create's callback has no error channel; a refusal may simply never call it.
export function create (backend, languages, namespace, timeout = 8000) {
  return new Promise((resolve) => {
    let done = false
    const finish = (value) => {
      if (done) return
      done = true
      clearTimeout(timer)
      resolve(value)
    }
    const timer = setTimeout(() => finish({ timeout: true }), timeout)
    try {
      backend.create(languages, namespace, 'key', 'value', (dataArray, resArray) => finish({ dataArray, resArray }))
    } catch (e) {
      finish({ threw: String((e && (e.message || e)) || e) })
    }
  })
}

export function valueOf (result) {
  return JSON.stringify(result)
}
