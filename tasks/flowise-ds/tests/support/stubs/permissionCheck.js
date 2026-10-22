// Offline stub of the RBAC middleware. It answers per permission string, like
// the real one: an organization admin passes, otherwise the caller's permission
// list must contain the exact permission the route asked for.
function denied(res) {
    return res.status(403).json({ message: 'Forbidden' })
}

const checkPermission = (permission) => (req, res, next) => {
    const user = req.user
    if (user) {
        if (user.isOrganizationAdmin) return next()
        const permissions = user.permissions
        if (permissions && permissions.includes(permission)) return next()
    }
    return denied(res)
}

const checkAnyPermission = (permissionsString) => (req, res, next) => {
    const user = req.user
    if (user) {
        if (user.isOrganizationAdmin) return next()
        const permissions = user.permissions
        const wanted = permissionsString.split(',')
        if (permissions && permissions.length) {
            for (const permission of wanted) {
                if (permissions.includes(permission)) return next()
            }
        }
    }
    return denied(res)
}

module.exports = { checkPermission, checkAnyPermission }
