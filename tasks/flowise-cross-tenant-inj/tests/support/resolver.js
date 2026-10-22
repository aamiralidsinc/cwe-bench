// Custom jest resolver. The product's utils barrel and getRunningExpressApp
// singleton are replaced by offline stubs regardless of how they are spelled
// (`./utils`, `../utils`, `../../utils/index`, `./getRunningExpressApp`, ...),
// so a helper added in a new directory still reaches the stubs instead of the
// real server module.
const path = require('path')

const PRODUCT_ROOT = process.env.PRODUCT_ROOT || '/app/packages/server/src'
const STUBS = path.join(__dirname, 'stubs')

const withoutExtension = (p) => String(p).replace(/\.(?:[cm]?[jt]sx?)$/, '')
const UTILS_BARREL = withoutExtension(path.join(PRODUCT_ROOT, 'utils', 'index'))
const RUNNING_APP = withoutExtension(path.join(PRODUCT_ROOT, 'utils', 'getRunningExpressApp'))

module.exports = (request, options) => {
    const resolved = options.defaultResolver(request, options)
    const base = withoutExtension(resolved)
    if (base === UTILS_BARREL) return path.join(STUBS, 'utils.js')
    if (base === RUNNING_APP) return path.join(STUBS, 'getRunningExpressApp.js')
    return resolved
}
