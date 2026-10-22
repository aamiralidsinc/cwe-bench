// Offline stub for the OpenAI SDK. Records each client's API key in
// globalThis.__openaiKeys and returns a universal proxy so any SDK method chain
// resolves without modelling individual endpoints. Never contacts the network.
function universal() {
    const target = function () {}
    return new Proxy(target, {
        get(_t, prop) {
            if (prop === 'then') return undefined
            if (prop === Symbol.iterator) return function* () {}
            if (prop === Symbol.asyncIterator) return function () { return { next: async () => ({ done: true, value: undefined }) } }
            if (prop === 'length') return 0
            return universal()
        },
        apply() { return Promise.resolve(universal()) }
    })
}
class OpenAIStub {
    constructor(opts) {
        const g = globalThis
        g.__openaiKeys = g.__openaiKeys || []
        g.__openaiKeys.push(opts && opts.apiKey)
        return universal()
    }
}
OpenAIStub.toFile = async () => ({})
module.exports = OpenAIStub
module.exports.default = OpenAIStub
