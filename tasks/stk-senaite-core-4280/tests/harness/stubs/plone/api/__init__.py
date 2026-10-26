"""Minimal ``plone.api`` facade backed by the harness security manager."""

from AccessControl import getSecurityManager


class _User(object):
    def has_permission(self, permission, obj=None):
        return getSecurityManager().checkPermission(permission, obj)

    def get_current_user(self):
        return getSecurityManager().getUser()

    def is_anonymous(self):
        return getSecurityManager().getUser().getId() == "Anonymous User"

    def get_roles(self, obj=None):
        return list(getSecurityManager().getUser().getRoles())


class _Portal(object):
    def get(self):
        from bika import _harness_portal
        return _harness_portal


class _Env(object):
    pass


user = _User()
portal = _Portal()
env = _Env()
