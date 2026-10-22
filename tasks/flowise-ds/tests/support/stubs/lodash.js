// Offline lodash stub: only the helpers the loaded product modules use.
const omit = (obj, keys) => {
    const out = { ...obj }
    for (const key of [].concat(keys)) delete out[key]
    return out
}
const cloneDeep = (value) => (value === undefined ? value : JSON.parse(JSON.stringify(value)))
const isEqual = (a, b) => JSON.stringify(a) === JSON.stringify(b)
const uniqWith = (arr, cmp) => {
    const out = []
    for (const item of arr) if (!out.some((seen) => cmp(item, seen))) out.push(item)
    return out
}
const get = (obj, path, fallback) => {
    let cur = obj
    for (const part of String(path).split('.')) {
        if (cur === null || cur === undefined) return fallback
        cur = cur[part]
    }
    return cur === undefined ? fallback : cur
}
const pick = (obj, keys) => {
    const out = {}
    for (const key of [].concat(keys)) if (key in obj) out[key] = obj[key]
    return out
}

module.exports = { omit, cloneDeep, isEqual, uniqWith, get, pick }
