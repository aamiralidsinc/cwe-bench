// jsdom has no EventSource; Livewire's dev hot-reload feature opens one at import time.
globalThis.__eventSources = []
if (! globalThis.EventSource) {
  globalThis.EventSource = class {
    constructor(url) { this.url = url; this._handlers = {}; globalThis.__eventSources.push(this) }
    addEventListener(name, cb) { (this._handlers[name] ||= []).push(cb) }
    emit(name, data) { for (const cb of this._handlers[name] || []) cb({ data: JSON.stringify(data) }) }
    removeEventListener() {}
    close() {}
  }
}

// jsdom does not implement object URLs. Record them instead; the download path builds one
// before it touches the DOM. `webkitURL` is the object the library prefers when present, and it
// keeps the recorder independent of whichever URL implementation the Node version exposes.
globalThis.__objectUrls = []
const objectUrlRecorder = {
  createObjectURL: (blob) => { globalThis.__objectUrls.push(blob); return 'blob:recorded' },
  revokeObjectURL: () => {},
}
if (globalThis.URL) {
  globalThis.URL.createObjectURL = objectUrlRecorder.createObjectURL
  globalThis.URL.revokeObjectURL = objectUrlRecorder.revokeObjectURL
}
globalThis.webkitURL = objectUrlRecorder
if (typeof window !== 'undefined') window.webkitURL = objectUrlRecorder

// No network in the verifier: answer every Livewire commit with each component's own
// snapshot and no effects, and record the payloads the page sent.
globalThis.__requests = []
globalThis.__pageFetches = []
globalThis.fetch = async (url, options = {}) => {
  if (! options.body) {
    globalThis.__pageFetches.push(String(url))
    return {
      status: 200, ok: true, redirected: false, url: String(url),
      headers: { has: () => false, get: () => null },
      text: async () => '<html><body><div id="next-page">next</div></body></html>',
    }
  }
  const body = JSON.parse(options.body)
  globalThis.__requests.push(body)
  const effects = globalThis.__responseEffects || { returns: [] }
  const components = body.components.map(c => ({ snapshot: c.snapshot, effects }))
  return {
    status: 200,
    ok: true,
    redirected: false,
    url: String(url),
    headers: { has: () => false, get: () => null },
    text: async () => JSON.stringify({ components, assets: {} }),
  }
}

// Every Livewire page carries a CSRF token and the update URI the script was served from.
document.head.insertAdjacentHTML('beforeend', '<meta name="csrf-token" content="test-token">')
document.head.insertAdjacentHTML('beforeend', '<script data-update-uri="/livewire/update" data-csrf="test-token"></script>')

globalThis.__reset = () => {
  globalThis.__requests.length = 0
  globalThis.__pageFetches.length = 0
  globalThis.__eventSources.length = 0
  globalThis.__objectUrls.length = 0
}
