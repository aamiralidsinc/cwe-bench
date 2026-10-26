def rolesForPermissionOn(permission, obj, default=None):
    allowed = obj.allowed_roles(permission) if hasattr(obj, "allowed_roles") else set()
    return sorted(allowed)
