// Express stub. The real router files call express.Router() and register
// (method, path(s), handlers). We record the registrations so a test can drive
// the real middleware + controller chain for a given method and URL.
function Router() {
    const routes = []
    const router = { __routes: routes }
    for (const method of ['get', 'post', 'put', 'delete', 'patch', 'use']) {
        router[method] = function (paths, ...handlers) {
            if (typeof paths === 'function') {
                handlers = [paths, ...handlers]
                paths = '/'
            }
            routes.push({ method, paths: [].concat(paths), handlers })
            return router
        }
    }
    return router
}

function express() {
    return { use() {}, get() {}, post() {}, set() {} }
}

express.Router = Router
module.exports = express
module.exports.default = express
module.exports.Router = Router
