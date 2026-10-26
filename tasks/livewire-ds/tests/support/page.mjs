// Shared page harness: builds the server-rendered DOM a Livewire page would carry,
// then starts the library exactly as a browser page does.

const PROTOTYPE_KEYS = [
  'html', 'scripts', 'js', 'xjs', 'dispatches', 'listeners', 'redirect',
  'redirectUsingNavigate', 'download', 'hotReload', 'returns', 'url',
  'lazyLoaded', 'isolate', 'probe',
]

export function snapshot(id, data, name = 'probe') {
  return JSON.stringify({ data, memo: { id, name, children: {} }, checksum: 'x' })
}

export function addComponent(id, data, effects, attrs = {}) {
  const el = document.createElement('div')
  el.setAttribute('wire:id', id)
  el.setAttribute('wire:snapshot', snapshot(id, data))
  el.setAttribute('wire:effects', JSON.stringify(effects))
  for (const [name, value] of Object.entries(attrs)) el.setAttribute(name, value)
  el.textContent = id
  document.body.appendChild(el)
  return el
}

// A server response is one entry per commit; a correct server always answers a call
// with an (empty) list of returned values.
export function respondWith(effects) {
  globalThis.__responseEffects = effects
}

export function resetPage(url = '/') {
  for (const key of PROTOTYPE_KEYS) {
    delete Object.prototype[key]
    delete Array.prototype[key]
  }
  document.body.innerHTML = ''
  globalThis.__requests.length = 0
  globalThis.__pageFetches.length = 0
  globalThis.__objectUrls.length = 0
  globalThis.__eventSources.length = 0
  globalThis.__responseEffects = undefined
  delete globalThis.Echo
  delete window.Echo
  window.history.replaceState({}, '', url)
}

export async function boot(settleMs = 80) {
  const { Livewire } = await import('@/index.js')
  Livewire.start()
  await new Promise(resolve => setTimeout(resolve, settleMs))
  return Livewire
}

export function query(...pairs) {
  return '/?' + pairs.join('&')
}

export function fragment(...pairs) {
  return '/#' + pairs.join('&')
}

// Bracket notation for one address parameter: bracket(['filters', '__proto__', 'html'], '<div>')
export function bracket(path, value) {
  const [first, ...rest] = path
  return first + rest.map(segment => `[${segment}]`).join('') + '=' + encodeURIComponent(value)
}

export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
