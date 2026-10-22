// Shared test harness.
//
// It installs a fake application server on globalThis: in-memory repositories
// with equality/operator matching for findOneBy/findOne/find/findBy/count, plus
// the singleton services the product code expects. The product's real routers,
// middleware and controllers run unchanged; only the infrastructure boundary
// (database, credential decryption, provider SDK, running-app singleton) is
// stubbed, as the project's own unit tests do.
const { Credential } = require('@product/database/entities/Credential')
const { WorkspaceShared } = require('@product/enterprise/database/entities/EnterpriseEntities')

const tables = new Map()

function rowsOf(entity) {
    if (!tables.has(entity)) tables.set(entity, [])
    return tables.get(entity)
}

function matchesValue(actual, condition) {
    if (condition && typeof condition === 'object' && !Array.isArray(condition)) {
        switch (condition.__op) {
            case 'equal':
                return actual === condition.value
            case 'in':
                return (condition.value || []).includes(actual)
            case 'not':
                return actual !== condition.value
            case 'isnull':
                return actual === null || actual === undefined
            case 'like':
                return new RegExp('^' + String(condition.value).replace(/%/g, '.*') + '$').test(String(actual))
            case 'morethan':
                return actual > condition.value
            case 'lessthan':
                return actual < condition.value
            default:
                break
        }
    }
    return actual === condition
}

function matchesWhere(row, where) {
    if (where === undefined || where === null) return true
    if (Array.isArray(where)) return where.some((clause) => matchesWhere(row, clause))
    return Object.entries(where).every(([key, value]) => matchesValue(row[key], value))
}

function whereOf(options) {
    if (options === undefined || options === null) return {}
    if (Object.prototype.hasOwnProperty.call(options, 'where')) return options.where
    return options
}

function notFound() {
    const error = new Error('EntityNotFoundError: could not find any entity matching the given criteria')
    error.name = 'EntityNotFoundError'
    return error
}

function repoFor(entity) {
    return {
        findOneBy: async (where) => rowsOf(entity).find((row) => matchesWhere(row, where)) || null,
        findOneByOrFail: async (where) => {
            const found = rowsOf(entity).find((row) => matchesWhere(row, where))
            if (!found) throw notFound()
            return found
        },
        findOne: async (options = {}) => rowsOf(entity).find((row) => matchesWhere(row, whereOf(options))) || null,
        findOneOrFail: async (options = {}) => {
            const found = rowsOf(entity).find((row) => matchesWhere(row, whereOf(options)))
            if (!found) throw notFound()
            return found
        },
        find: async (options = {}) => rowsOf(entity).filter((row) => matchesWhere(row, whereOf(options))),
        findBy: async (where) => rowsOf(entity).filter((row) => matchesWhere(row, where)),
        count: async (options = {}) => rowsOf(entity).filter((row) => matchesWhere(row, whereOf(options))).length,
        countBy: async (where) => rowsOf(entity).filter((row) => matchesWhere(row, where)).length,
        exists: async (options = {}) => rowsOf(entity).some((row) => matchesWhere(row, whereOf(options))),
        existsBy: async (where) => rowsOf(entity).some((row) => matchesWhere(row, where)),
        create: (value) => (Array.isArray(value) ? value.map((item) => ({ ...item })) : { ...value }),
        save: async (value) => {
            const rows = rowsOf(entity)
            const items = Array.isArray(value) ? value : [value]
            for (const item of items) {
                const existing = item && item.id ? rows.find((row) => row.id === item.id) : undefined
                if (existing) Object.assign(existing, item)
                else rows.push({ ...item, id: item && item.id ? item.id : 'row_' + Math.random().toString(36).slice(2) })
            }
            return value
        },
        insert: async (value) => {
            const rows = rowsOf(entity)
            const items = Array.isArray(value) ? value : [value]
            for (const item of items) rows.push({ ...item })
            return { identifiers: items }
        },
        delete: async (criteria) => {
            const rows = rowsOf(entity)
            let affected = 0
            for (let i = rows.length - 1; i >= 0; i -= 1) {
                if (matchesWhere(rows[i], criteria)) {
                    rows.splice(i, 1)
                    affected += 1
                }
            }
            return { affected }
        },
        update: async (criteria, partial) => {
            let affected = 0
            for (const row of rowsOf(entity)) {
                if (matchesWhere(row, criteria)) {
                    Object.assign(row, partial)
                    affected += 1
                }
            }
            return { affected }
        },
        merge: (target, source) => Object.assign(target, source),
        createQueryBuilder: () => {
            throw new Error('the verifier repository does not model query builders')
        }
    }
}

function resetHarness() {
    tables.clear()
    tables.set(Credential, [])
    tables.set(WorkspaceShared, [])
    const g = globalThis
    g.__openaiKeys = []
    g.__openaiClients = []
    g.__decryptCalls = []
    g.__APPSERVER = {
        AppDataSource: {
            getRepository: (entity) => repoFor(entity),
            manager: { getRepository: (entity) => repoFor(entity) },
            transaction: async (fn) => fn({ manager: { getRepository: (entity) => repoFor(entity) } })
        },
        nodesPool: { componentCredentials: {}, componentNodes: {} },
        telemetry: { sendTelemetry: async () => {} },
        metricsProvider: { incrementCounter: () => {} },
        usageCacheManager: {},
        abortControllerPool: { add: () => {}, remove: () => {} },
        identityManager: {}
    }
}

function seedCredential(credential) {
    rowsOf(Credential).push({
        name: 'credential',
        credentialName: 'openAIApi',
        createdDate: new Date('2026-01-01T00:00:00Z'),
        updatedDate: new Date('2026-01-01T00:00:00Z'),
        ...credential
    })
}

function seedShare(share) {
    rowsOf(WorkspaceShared).push({
        id: 'share_' + Math.random().toString(36).slice(2),
        itemType: 'credential',
        ...share
    })
}

function openaiKeys() {
    return globalThis.__openaiKeys || []
}

function decryptCalls() {
    return globalThis.__decryptCalls || []
}

function makeReq(overrides = {}) {
    return {
        query: {},
        params: {},
        body: {},
        headers: {},
        protocol: 'http',
        get: () => 'localhost',
        ...overrides
    }
}

function makeRes() {
    const res = { statusCode: 200, body: undefined, jsonCalled: false, headers: {}, sent: undefined }
    res.status = (code) => {
        res.statusCode = code
        return res
    }
    res.json = (body) => {
        res.jsonCalled = true
        res.body = body
        return res
    }
    res.send = (body) => {
        res.jsonCalled = true
        res.body = body
        return res
    }
    res.sendStatus = (code) => {
        res.statusCode = code
        res.jsonCalled = true
        return res
    }
    res.setHeader = (name, value) => {
        res.headers[name] = value
        return res
    }
    res.write = () => true
    res.end = () => res
    return res
}

function normalizePath(value) {
    const path = String(value).split('?')[0].replace(/\/+$/, '')
    return path === '' ? '/' : path
}

function matchPath(pattern, url) {
    if (typeof pattern !== 'string') return null
    const wanted = normalizePath(pattern)
    const actual = normalizePath(url)
    if (wanted === actual) return {}
    const wantedSegments = wanted.split('/').filter(Boolean)
    const actualSegments = actual.split('/').filter(Boolean)
    if (wantedSegments.length !== actualSegments.length) return null
    const params = {}
    for (let i = 0; i < wantedSegments.length; i += 1) {
        const segment = wantedSegments[i]
        if (segment.startsWith(':')) params[segment.slice(1)] = decodeURIComponent(actualSegments[i])
        else if (segment !== actualSegments[i]) return null
    }
    return params
}

function matchPrefix(pattern, url) {
    if (typeof pattern !== 'string') return null
    const wanted = normalizePath(pattern)
    const actual = normalizePath(url)
    if (wanted === '/') return {}
    const wantedSegments = wanted.split('/').filter(Boolean)
    const actualSegments = actual.split('/').filter(Boolean)
    if (wantedSegments.length > actualSegments.length) return null
    const params = {}
    for (let i = 0; i < wantedSegments.length; i += 1) {
        const segment = wantedSegments[i]
        if (segment.startsWith(':')) params[segment.slice(1)] = decodeURIComponent(actualSegments[i])
        else if (segment !== actualSegments[i]) return null
    }
    return params
}

// Find the first registered route for method+url, extract its path params, then
// run any matching router-level middleware (router.use) followed by the route's
// real middleware/controller chain. `next` receives any forwarded error.
async function dispatch(router, method, url, req, res, next) {
    const routes = router && router.__routes ? router.__routes : []
    let found = null
    for (const route of routes) {
        if (route.method !== method) continue
        for (const pattern of route.paths) {
            const params = matchPath(pattern, url)
            if (params !== null) {
                found = { route, params }
                break
            }
        }
        if (found) break
    }
    if (!found) throw new Error(`no route registered for ${method.toUpperCase()} ${url}`)
    const applied = []
    for (const route of routes) {
        if (route.method !== 'use') continue
        for (const pattern of route.paths) {
            const params = matchPrefix(pattern, url)
            if (params !== null) {
                applied.push({ route, params })
                break
            }
        }
    }
    applied.push(found)
    req.params = Object.assign({}, req.params || {})
    for (const { route, params } of applied) {
        Object.assign(req.params, params)
        for (const handler of route.handlers) {
            let advanced = false
            let forwarded
            const step = (error) => {
                advanced = true
                forwarded = error
            }
            try {
                await handler(req, res, step)
            } catch (error) {
                next(error)
                return
            }
            if (forwarded) {
                next(forwarded)
                return
            }
            if (!advanced) return
        }
    }
    next()
}

function sessionUser(workspaceId, organizationId = 'org_default', extra = {}) {
    return {
        id: `user_${workspaceId}`,
        activeWorkspaceId: workspaceId,
        activeOrganizationId: organizationId,
        isOrganizationAdmin: true,
        ...extra
    }
}

function apiKeyUser(workspaceId, organizationId, permissions) {
    return {
        activeWorkspaceId: workspaceId,
        activeOrganizationId: organizationId,
        isOrganizationAdmin: false,
        permissions
    }
}

// The attack is blocked when the foreign secret was neither decrypted nor handed
// to the provider SDK, and the caller received a client error.
function expectBlocked(res, next, secret) {
    expect(decryptCalls()).not.toContain(secret)
    expect(openaiKeys()).not.toContain(secret)
    const error = next.mock.calls.length ? next.mock.calls[0][0] : undefined
    const status = (error && (error.statusCode || error.status)) || res.statusCode
    expect(typeof status).toBe('number')
    expect(status).toBeGreaterThanOrEqual(400)
    expect(status).toBeLessThan(500)
}

// Legitimate use succeeded and the caller's own/shared secret was used.
function expectAllowed(res, next, secret) {
    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBeLessThan(400)
    expect(res.jsonCalled).toBe(true)
    expect(decryptCalls()).toContain(secret)
}

function expectProviderUsed(next, secret) {
    expect(next).not.toHaveBeenCalled()
    expect(openaiKeys()).toContain(secret)
}

module.exports = {
    resetHarness,
    seedCredential,
    seedShare,
    openaiKeys,
    decryptCalls,
    makeReq,
    makeRes,
    dispatch,
    sessionUser,
    apiKeyUser,
    expectBlocked,
    expectAllowed,
    expectProviderUsed
}
