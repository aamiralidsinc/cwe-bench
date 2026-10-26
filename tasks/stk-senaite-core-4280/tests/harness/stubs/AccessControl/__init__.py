"""Minimal AccessControl model used by the offline harness.

A fake content object answers ``allowed_roles(permission)`` (roles that hold the
permission on it, inherited from its parent).  The current SecurityManager holds
the roles of the signed-in user.
"""

import AccessControl.Permissions  # noqa: F401  (make the submodule importable)


class Unauthorized(Exception):
    pass


class _AnonymousUser(object):
    def getId(self):
        return "Anonymous User"

    def getUserName(self):
        return "Anonymous User"

    def getRolesInContext(self, obj=None):
        return ["Anonymous"]

    def getRoles(self):
        return ["Anonymous"]


class _User(object):
    def __init__(self, userid, roles):
        self._userid = userid
        self._roles = list(roles)

    def getId(self):
        return self._userid

    def getUserName(self):
        return self._userid

    def getRoles(self):
        return list(self._roles)

    def getRolesInContext(self, obj=None):
        return list(self._roles)

    def __repr__(self):
        return "<User %s %r>" % (self._userid, self._roles)


class SecurityManager(object):
    def __init__(self, user=None):
        self._user = user or _AnonymousUser()

    def getUser(self):
        return self._user

    def getAuthenticatedUser(self):
        return self._user

    def checkPermission(self, permission, object, context=None):
        if object is None:
            return False
        if permission in ("View", "zope2.View", "Access contents information"):
            return True
        if hasattr(object, "allowed_roles"):
            allowed = object.allowed_roles(permission)
        else:
            allowed = set()
        return bool(allowed.intersection(self._user.getRoles()))

    def validate(self, *args, **kwargs):
        return 1

    def addContext(self, object):
        return object

    def removeContext(self, object):
        return None


_anonymous_manager = SecurityManager()


def getSecurityManager():
    return _anonymous_manager


def setSecurityManager(manager):
    global _anonymous_manager
    _anonymous_manager = manager


def allow_module(*args, **kwargs):
    return None


def allow_class(*args, **kwargs):
    return None


class ModuleSecurityInfo(object):
    def __init__(self, name=""):
        self.name = name

    def declarePublic(self, *names):
        return None

    def declarePrivate(self, *names):
        return None


class ClassSecurityInfo(object):
    def declarePublic(self, *names):
        def decorator(func):
            return func
        return decorator

    def declarePrivate(self, *names):
        def decorator(func):
            return func
        return decorator

    def declareProtected(self, permission, *names):
        def decorator(func):
            return func
        return decorator

    def declareClassPublic(self, *names):
        return None

    def declareClassPrivate(self, *names):
        return None

    def declareClassProtected(self, permission, *names):
        return None

    def apply(self, object):
        return object
