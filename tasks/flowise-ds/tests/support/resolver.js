// Jest resolver used by the verifier.
//
// The product modules import a lot of server infrastructure (the running-app
// singleton, the utils barrel, the logger, config-dependent constants, the RBAC
// middleware, workspace services). None of it is needed to exercise the tested
// request handlers, and several of those modules cannot be loaded offline. We
// resolve modules normally first, then redirect the infrastructure by its
// RESOLVED ABSOLUTE PATH. Redirecting by path (rather than by the literal
// specifier) means a fix that adds a new helper file importing the same
// infrastructure is still routed to the stubs.
const path = require('path')

const STUB = path.join(__dirname, 'stubs')

const BARE = {
    openai: 'openai.js',
    'flowise-components': 'flowise-components.js',
    express: 'express.js',
    typeorm: 'typeorm.js',
    'content-disposition': 'content-disposition.js',
    axios: 'axios.js',
    lodash: 'lodash.js',
    winston: 'winston.js',
    'zod/v3': 'zod.js',
    uuid: 'uuid.js'
}

const PATH_RULES = [
    [/\/utils\/getRunningExpressApp(?:\.(?:ts|js))?$/, 'getRunningExpressApp.js'],
    [/\/utils\/fileValidation(?:\.(?:ts|js))?$/, 'fileValidation.js'],
    [/\/utils\/logger(?:\.(?:ts|js))?$/, 'logger.js'],
    [/\/utils\/constants(?:\.(?:ts|js))?$/, 'constants.js'],
    [/\/utils\/index(?:\.(?:ts|js))?$/, 'utils.js'],
    [/\/enterprise\/rbac\/PermissionCheck(?:\.(?:ts|js))?$/, 'permissionCheck.js'],
    [/\/enterprise\/services\/workspace\.service(?:\.(?:ts|js))?$/, 'workspaceService.js'],
    [/\/enterprise\/services\/organization-user\.service(?:\.(?:ts|js))?$/, 'organizationUserService.js'],
    [/\/enterprise\/Interface\.Enterprise(?:\.(?:ts|js))?$/, 'interfaceEnterprise.js']
]

module.exports = (request, options) => {
    if (Object.prototype.hasOwnProperty.call(BARE, request)) {
        return path.join(STUB, BARE[request])
    }
    const resolved = options.defaultResolver(request, options)
    const normalized = String(resolved).replace(/\\/g, '/')
    for (const [pattern, stub] of PATH_RULES) {
        if (pattern.test(normalized)) return path.join(STUB, stub)
    }
    return resolved
}
