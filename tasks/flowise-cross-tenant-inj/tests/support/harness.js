// Shared test harness. Installs a fake app server (in-memory repositories with
// the finder surface the project's services use) on globalThis, and provides
// helpers to seed credentials / workspace shares and to fabricate Express
// req/res/next objects. The product's real controllers and services run
// unchanged; only the infrastructure boundary is stubbed, as the project's own
// unit tests do.
const { Credential } = require('@product/database/entities/Credential')
const { WorkspaceShared } = require('@product/enterprise/database/entities/EnterpriseEntities')

const tables = new Map()

function rowsOf(entity) {
    if (!tables.has(entity)) tables.set(entity, [])
    return tables.get(entity)
}

// Equality as TypeORM applies it: undefined conditions are ignored, an array is
// an IN list, and the operator objects exported by typeorm (In, Not, Like,
// IsNull) are honoured.
function fieldMatches(value, expected) {
    if (expected === undefined) return true
    if (Array.isArray(expected)) return expected.some((e) => fieldMatches(value, e))
    if (expected && typeof expected === 'object') {
        switch (expected._type) {
            case 'in':
                return Array.isArray(expected.value) && expected.value.includes(value)
            case 'not':
                return !fieldMatches(value, expected.value)
            case 'like': {
                const source = String(expected.value ?? '')
                const pattern = source.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/%/g, '.*').replace(/_/g, '.')
                return new RegExp(`^${pattern}$`).test(String(value ?? ''))
            }
            case 'isnull':
                return value === null || value === undefined
            default:
                break
        }
    }
    return value === expected
}

// `where` may be a plain object or an array of objects (OR).
function matches(row, where) {
    if (Array.isArray(where)) return where.some((w) => matches(row, w))
    if (!where || typeof where !== 'object') return true
    return Object.entries(where).every(([key, value]) => fieldMatches(row[key], value))
}

function whereOf(opts) {
    if (Array.isArray(opts)) return opts
    if (opts && typeof opts === 'object' && 'where' in opts) return opts.where || {}
    return opts || {}
}

// Minimal TypeORM query-builder support: string conditions of the form
// `alias.column = :param`, `alias.column != :param` and
// `alias.column IN (:...param)`, joined with AND / OR. A plain object is also
// accepted, as are the common chainable no-ops. Enough for a fix written with
// createQueryBuilder instead of a repository finder.
function parseCondition(expr) {
    const text = String(expr).trim()
    let m = text.match(/^(?:\w+\.)?(\w+)\s+IN\s*\(\s*:\.\.\.(\w+)\s*\)$/i)
    if (m) return (row, params) => fieldMatches(row[m[1]], params[m[2]])
    m = text.match(/^(?:\w+\.)?(\w+)\s*(=|!=|<>)\s*:(\w+)$/)
    if (m) {
        return (row, params) => {
            const equal = row[m[1]] === params[m[3]]
            return m[2] === '=' ? equal : !equal
        }
    }
    return null
}

function compileCondition(expr) {
    if (expr && typeof expr === 'object') return (row) => matches(row, expr)
    const parts = String(expr).split(/\s+(AND|OR)\s+/i)
    const steps = []
    for (let i = 0; i < parts.length; i += 2) {
        const test = parseCondition(parts[i])
        if (!test) throw new Error(`unsupported query-builder condition: ${expr}`)
        steps.push({ test, join: i === 0 ? null : parts[i - 1].toUpperCase() })
    }
    return (row, params) => {
        let result = null
        for (const step of steps) {
            const value = step.test(row, params)
            if (result === null) result = value
            else if (step.join === 'OR') result = result || value
            else result = result && value
        }
        return Boolean(result)
    }
}

function queryBuilderFor(entity) {
    const conditions = []
    let limit = 0
    const builder = {
        where(expr, params) {
            conditions.push({ test: compileCondition(expr), params: params || {} })
            return builder
        },
        andWhere(expr, params) {
            return builder.where(expr, params)
        },
        orWhere(expr, params) {
            return builder.where(expr, params)
        },
        select() {
            return builder
        },
        addSelect() {
            return builder
        },
        from() {
            return builder
        },
        innerJoin() {
            return builder
        },
        leftJoin() {
            return builder
        },
        innerJoinAndSelect() {
            return builder
        },
        leftJoinAndSelect() {
            return builder
        },
        orderBy() {
            return builder
        },
        addOrderBy() {
            return builder
        },
        skip() {
            return builder
        },
        offset() {
            return builder
        },
        limit(n) {
            limit = Number(n) || 0
            return builder
        },
        take(n) {
            limit = Number(n) || 0
            return builder
        },
        getOne: async () => run()[0] || null,
        getMany: async () => run(),
        getManyAndCount: async () => {
            const rows = run()
            return [rows, rows.length]
        },
        getCount: async () => run().length,
        getExists: async () => run().length > 0
    }
    function run() {
        const rows = rowsOf(entity).filter((row) => conditions.every((c) => c.test(row, c.params)))
        return limit > 0 ? rows.slice(0, limit) : rows
    }
    return builder
}

function repoFor(entity) {
    const all = () => rowsOf(entity)
    const select = (opts) => all().filter((row) => matches(row, whereOf(opts)))
    const firstOrFail = (opts) => {
        const row = select(opts)[0]
        if (!row) throw new Error(`EntityNotFoundError: ${entity.name || 'entity'} not found`)
        return row
    }
    return {
        findOneBy: async (where) => select(where)[0] || null,
        findOne: async (opts = {}) => select(opts)[0] || null,
        findOneByOrFail: async (where) => firstOrFail(where),
        findOneOrFail: async (opts = {}) => firstOrFail(opts),
        find: async (opts = {}) => select(opts),
        findBy: async (where) => select(where),
        findAndCount: async (opts = {}) => {
            const rows = select(opts)
            return [rows, rows.length]
        },
        count: async (opts = {}) => select(opts).length,
        countBy: async (where) => select(where).length,
        exists: async (opts = {}) => select(opts).length > 0,
        existsBy: async (where) => select(where).length > 0,
        create: (x) => ({ ...x }),
        save: async (x) => {
            const rows = Array.isArray(x) ? x : [x]
            rows.forEach((row) => all().push(row))
            return x
        },
        insert: async (x) => {
            const rows = Array.isArray(x) ? x : [x]
            rows.forEach((row) => all().push(row))
            return { identifiers: [], generatedMaps: [] }
        },
        update: async () => ({ affected: 1 }),
        delete: async () => ({ affected: 1 }),
        remove: async (x) => x,
        createQueryBuilder: () => queryBuilderFor(entity)
    }
}

function resetHarness() {
    tables.clear()
    tables.set(Credential, [])
    tables.set(WorkspaceShared, [])
    const g = globalThis
    g.__openaiKeys = []
    g.__decryptCalls = []
    g.__APPSERVER = {
        nodesPool: {},
        telemetry: {},
        AppDataSource: { getRepository: (e) => repoFor(e) }
    }
}
function seedCredential(c) {
    rowsOf(Credential).push({ name: 'cred', credentialName: 'openAIApi', ...c })
}
function seedShare(s) {
    rowsOf(WorkspaceShared).push({ id: 's_' + Math.random().toString(36).slice(2), itemType: 'credential', ...s })
}
function openaiKeys() {
    return globalThis.__openaiKeys || []
}
function decryptCalls() {
    return globalThis.__decryptCalls || []
}
function makeReq(o = {}) {
    return { query: {}, params: {}, body: {}, ...o }
}
function makeRes() {
    const res = { statusCode: 200, body: undefined, jsonCalled: false, headers: {} }
    res.status = (c) => {
        res.statusCode = c
        return res
    }
    res.json = (b) => {
        res.jsonCalled = true
        res.body = b
        return res
    }
    res.send = (b) => {
        res.jsonCalled = true
        res.body = b
        return res
    }
    res.sendStatus = (c) => {
        res.statusCode = c
        res.jsonCalled = true
        return res
    }
    res.end = () => res
    res.setHeader = (k, v) => {
        res.headers[k] = v
        return res
    }
    return res
}

// A request for a credential the caller may not use must not touch the secret,
// and it must be refused as a client error. The refusal may be delivered either
// way the project already uses: an error passed to next() carrying a 4xx status,
// or a 4xx written on the response. A crash or a 500 is not a client error.
function expectBlocked(res, next, secret) {
    expect(openaiKeys()).not.toContain(secret)
    expect(decryptCalls()).not.toContain(secret)
    const error = next.mock.calls.length > 0 ? next.mock.calls[0][0] : undefined
    const status = error && typeof error === 'object' ? (error.statusCode ?? error.status) : undefined
    const refusedViaNext = typeof status === 'number' && status >= 400 && status < 500
    const refusedViaRes = res.statusCode >= 400 && res.statusCode < 500
    if (!refusedViaNext && !refusedViaRes) {
        throw new Error(`expected a 4xx refusal; next() got ${String(status)}, response got ${res.statusCode}`)
    }
}

module.exports = {
    resetHarness,
    seedCredential,
    seedShare,
    openaiKeys,
    decryptCalls,
    makeReq,
    makeRes,
    expectBlocked
}
