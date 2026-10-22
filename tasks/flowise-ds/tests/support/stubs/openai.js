// Offline OpenAI SDK stub.
//
// Every client's API key is recorded in globalThis.__openaiKeys, so a test can
// tell whether a stored secret was handed to the provider SDK. Method chains
// resolve to objects without touching the network; the handful of endpoints the
// tested product code reads are modelled explicitly.
function resultFor(parts, args) {
    const p = parts.join('.')
    if (p === 'vectorStores.fileBatches.createAndPoll') {
        const batch = args[1] || {}
        const n = Array.isArray(batch.file_ids) ? batch.file_ids.length : 0
        return { status: 'completed', file_counts: { completed: n, failed: 0, total: n } }
    }
    if (p === 'files.create') return { id: 'file_stub_1' }
    if (p === 'files.list') return { data: [] }
    if (p === 'models.list') return { data: [] }
    if (p === 'beta.threads.create') return { id: 'thread_stub_1' }
    if (p.endsWith('.list')) return { data: [] }
    if (p.endsWith('.retrieve')) return { id: 'assistant_stub_1', tool_resources: {} }
    if (p.endsWith('.delete')) return { deleted: true, id: 'deleted_stub' }
    if (p.endsWith('.create')) return { id: 'created_stub' }
    if (p.endsWith('.update')) return { id: 'updated_stub' }
    return { id: 'stub' }
}

function node(parts) {
    const fn = function (...args) {
        return Promise.resolve(resultFor(parts, args))
    }
    return new Proxy(fn, {
        get(_target, prop) {
            if (prop === 'then') return undefined
            if (prop === Symbol.iterator) return function* () {}
            if (prop === Symbol.asyncIterator) {
                return function () {
                    return { next: async () => ({ done: true, value: undefined }) }
                }
            }
            return node([...parts, String(prop)])
        },
        apply(_target, _this, args) {
            return fn(...args)
        }
    })
}

class OpenAIStub {
    constructor(opts) {
        const g = globalThis
        g.__openaiKeys = g.__openaiKeys || []
        g.__openaiKeys.push(opts && opts.apiKey)
        return node([])
    }
}

OpenAIStub.toFile = async () => ({})
module.exports = OpenAIStub
module.exports.default = OpenAIStub
